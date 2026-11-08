# SPDX-License-Identifier: Apache-2.0
"""Verify the prospective sweep using public frozen inputs only."""

import asyncio
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import time

import pytest

from script.eval.evidence import create_evidence_store
from script.eval.inputs import GitRepositoryReader
from script.eval.model import (
    DirectoryOption,
    FrozenInputs,
    HarnessConfig,
    InstructionsSnapshot,
    SourceSnapshot,
)
from script.eval.plan import PurePlanBuilder
from script.eval.runner.adapters import (
    CodexAttemptRequestBuilder,
    CodexCliBindingResolver,
)
from script.eval.runner.adapters.codex import requested_settings
from script.eval.runner.ports import CliBinding
from script.reviewer_eval import concurrency_sweep
from script.reviewer_eval.concurrency_sweep import (
    SweepPlanBuilder,
    configuration,
    frozen_manifest,
)
from script.reviewer_eval.report import inspect_evidence, inspect_run
from script.reviewer_eval.sweep_manifest import MANIFEST, generate


def public_inputs(config: HarnessConfig) -> FrozenInputs:
    """Build public snapshots directly for a pure offline plan.

    Returns:
        Frozen snapshots for the configured directories.
    """
    snapshots = []
    for option in config.ordered_options:
        assert isinstance(option, DirectoryOption)
        for path in sorted(option.path.iterdir()):
            content = path.read_bytes()
            snapshots.append(
                SourceSnapshot(
                    directory_position=option.position,
                    repository_path=str(path),
                    commit_blob_sha="0" * 40,
                    content_sha256=sha256(content).hexdigest(),
                    content=content,
                )
            )
    return FrozenInputs(Path.cwd(), "head", tuple(snapshots), None)


def test_selection_reconstructs_exact_public_c_prompts() -> None:
    """The selection is an ordered subset of the ordinary C matrix."""
    config = configuration(1, None)
    inputs = public_inputs(config)
    pairs = frozen_manifest()["pairs"]
    full = PurePlanBuilder("run").plan(inputs, config)
    selected = SweepPlanBuilder("run", pairs).plan(inputs, config)
    by_context = {call.context_indices: call for call in full.calls}
    assert len(full.calls) == 186
    assert len(selected.calls) == 50
    assert all(
        call.prompt == by_context[call.context_indices].prompt
        for call in selected.calls
    )
    assert [call.position for call in selected.calls] == list(range(50))
    altered = [{**pairs[0], "prompt_sha256": "0" * 64}, *pairs[1:]]
    with pytest.raises(ValueError, match="prompt drift"):
        SweepPlanBuilder("run", altered).plan(inputs, config)
    with pytest.raises(ValueError, match="configuration drift"):
        SweepPlanBuilder("run", pairs).plan(
            inputs, config.model_copy(update={"efforts": ("low",)})
        )


async def test_saved_reader_requires_the_explicit_frozen_planner(
    tmp_path: Path,
) -> None:
    """Only the explicit trusted selection reconstructs the saved 50-call plan."""
    output = tmp_path / "evidence"
    config = configuration(1, output)
    inputs = public_inputs(config)
    pairs = frozen_manifest()["pairs"]
    plan = SweepPlanBuilder("run", pairs).plan(inputs, config)
    await create_evidence_store().create(output, plan)
    assert inspect_run(output).evidence_state == "invalid"
    assert (
        inspect_evidence(
            output, planner_factory=lambda run_id: SweepPlanBuilder(run_id, pairs)
        ).plan
        == plan
    )
    plan_path = output / "plan.json"
    tampered = json.loads(plan_path.read_bytes())
    tampered["calls"][0], tampered["calls"][1] = (
        tampered["calls"][1],
        tampered["calls"][0],
    )
    plan_path.write_text(json.dumps(tampered))
    assert (
        inspect_evidence(
            output, planner_factory=lambda run_id: SweepPlanBuilder(run_id, pairs)
        ).plan
        is None
    )


async def test_dry_run_has_no_cli_binding_or_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The real composition estimates the selected schedule without binding."""
    content = concurrency_sweep.INSTRUCTIONS.read_bytes()

    def freeze(_self: GitRepositoryReader, config: HarnessConfig) -> FrozenInputs:
        return replace(
            public_inputs(config),
            instructions_file=InstructionsSnapshot(
                repository_path=str(concurrency_sweep.INSTRUCTIONS),
                commit_blob_sha="0" * 40,
                content_sha256=sha256(content).hexdigest(),
                content=content,
            ),
        )

    def refuse_binding(
        _self: CodexCliBindingResolver, _config: HarnessConfig
    ) -> CliBinding:
        raise AssertionError("dry run must not resolve a CLI binding")

    monkeypatch.setattr(GitRepositoryReader, "freeze", freeze)
    monkeypatch.setattr(CodexCliBindingResolver, "resolve", refuse_binding)
    report = await concurrency_sweep.prepare(frozen_manifest()["pairs"])
    assert report.scheduled_call_count == 50
    assert all(estimate.instructions_file is not None for estimate in report.estimates)
    assert not any(tmp_path.iterdir())


async def test_selected_request_uses_empty_stdin_and_fixed_bounds(
    tmp_path: Path,
) -> None:
    """The request builder keeps the schedule out of a child process's stdin."""
    output = tmp_path / "evidence"
    config = configuration(25, output)
    plan = SweepPlanBuilder("run", frozen_manifest()["pairs"]).plan(
        public_inputs(config), config
    )
    evidence = await create_evidence_store().create(output, plan)
    binding = CliBinding(
        Path("/fake/codex"),
        "codex-cli 0.166.0",
        "test",
        requested_settings(config, Path.cwd(), None),
        None,
    )
    request = (
        CodexAttemptRequestBuilder(invocation_cwd=tmp_path)
        .build(plan, plan.calls[0], binding, evidence, config)
        .request
    )
    assert request.stdin == "devnull"
    assert request.timeout_seconds == 300
    assert request.cleanup_timeout_seconds == 10
    assert request.output_limit_bytes == 1024 * 1024
    assert config.retry_limit == config.capacity_retry_limit == 0
    assert not config.quota_wait_enabled


async def test_deadline_cancels_and_settles_owned_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The wall bound cancels the active operation and waits for its cleanup."""
    from script.eval.evidence_status import EvidenceStatus
    from script.eval.model import DryRunReport, RunRecord

    cleaned = asyncio.Event()

    async def blocked(
        _config: HarnessConfig,
        _status: EvidenceStatus,
        _pairs: list[dict[str, object]],
        _expected: tuple[str, str],
    ) -> DryRunReport | RunRecord:
        try:
            await asyncio.Event().wait()
        finally:
            cleaned.set()
        raise AssertionError("unreachable")

    monkeypatch.setattr(concurrency_sweep, "execute_block", blocked)
    status = EvidenceStatus(create_evidence_store)
    code = await concurrency_sweep.timed_block(
        configuration(1, tmp_path / "block"),
        status,
        [],
        ("fake", "version"),
        time.monotonic() + 0.05,
    )
    assert code == 130
    assert cleaned.is_set()


def test_frozen_manifest_and_schedule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The checked-in manifest is regenerated exactly and plans 600 calls."""
    assert MANIFEST.read_bytes() == generate()
    manifest = frozen_manifest()
    assert len(manifest["pairs"]) == 50
    assert [block["concurrency"] for block in manifest["blocks"]] == [
        1,
        5,
        10,
        25,
        5,
        10,
        25,
        1,
        10,
        25,
        1,
        5,
    ]
    changed = tmp_path / "manifest.json"
    changed.write_bytes(MANIFEST.read_bytes() + b" ")
    monkeypatch.setattr(concurrency_sweep, "MANIFEST", changed)
    with pytest.raises(ValueError, match="drifted"):
        frozen_manifest()


def test_existing_evidence_root_is_refused(tmp_path: Path) -> None:
    """An existing destination cannot be overwritten or resumed."""
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        concurrency_sweep.fresh_output_path(existing)
    assert list(existing.iterdir()) == []


@pytest.mark.parametrize("status", [1, 3, 130])
def test_failed_or_cancelled_block_stops_schedule_and_keeps_timing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    """No next block starts after a nonzero settled result."""
    manifest = frozen_manifest()
    monkeypatch.setattr(concurrency_sweep, "frozen_manifest", lambda: manifest)
    monkeypatch.setattr(concurrency_sweep, "head", lambda: "head")
    monkeypatch.setattr(concurrency_sweep, "cli", lambda: ("/fake/codex", "version"))
    starts: list[int] = []

    async def fake_block(
        config: HarnessConfig,
        _status: object,
        _pairs: object,
        _executable: object,
        _deadline: float,
    ) -> int:
        await asyncio.sleep(0)
        starts.append(config.concurrency)
        return status

    monkeypatch.setattr(concurrency_sweep, "timed_block", fake_block)
    with asyncio.Runner() as runner:
        result = concurrency_sweep.run_schedule(
            runner,
            manifest,
            tmp_path,
            "head",
            ("/fake/codex", "version"),
            time.monotonic() + 10,
            1024 * 1024 * 1024,
        )
    assert result == status
    assert starts == [1]
    timing = json.loads((tmp_path / "01-rep1-c1.timing.json").read_bytes())
    assert timing["end_monotonic"] >= timing["start_monotonic"]
    assert timing["elapsed_seconds"] >= 0
    assert time.monotonic() >= timing["end_monotonic"]


@pytest.mark.parametrize("valid", [48, 49])
def test_block_public_validity_threshold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid: int
) -> None:
    """Exactly 49 valid results can continue; fewer stop the schedule."""
    from script.eval.model import RunRecord
    from script.reviewer_eval.report import Counts, Inspection, Report

    pairs = frozen_manifest()["pairs"]
    config = configuration(1, tmp_path)
    plan = SweepPlanBuilder("run", pairs).plan(public_inputs(config), config)
    report = Report(
        evidence_state="complete",
        diagnostic=None,
        run_id="run",
        head_commit="head",
        planned_count=50,
        counts=Counts(
            complete=valid, incomplete=0, invalid=50 - valid, failed=0, not_started=0
        ),
        calls=(),
    )

    def fake_inspection(_root: Path, *, planner_factory: object) -> Inspection:
        del planner_factory
        return Inspection(plan, report)

    monkeypatch.setattr(concurrency_sweep, "inspect_evidence", fake_inspection)
    run = RunRecord(
        run_id="run",
        repository_root="/unused",
        head_commit="head",
        state="complete",
        runner_version="test",
        codex_path="/fake/codex",
        cli_version="codex-cli 0.166.0",
        effective_settings=(),
        calls=(),
    )
    (tmp_path / "run.json").write_text(run.model_dump_json())
    if valid < 49:
        with pytest.raises(ValueError, match="below 49"):
            concurrency_sweep.check_block(
                tmp_path, pairs, ("/fake/codex", "codex-cli 0.166.0")
            )
    else:
        concurrency_sweep.check_block(
            tmp_path, pairs, ("/fake/codex", "codex-cli 0.166.0")
        )


async def test_stream_audit_accepts_transport_and_stops_tool_activity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A known transport notice is allowed, while a tool event stops the block."""
    from script.reviewer_eval.report import Counts, Inspection
    from test.script.integration.reviewer_eval.support import create_run

    root = tmp_path / "run"
    await create_run(root)
    original = inspect_evidence(root)
    assert original.plan is not None
    report = original.report.model_copy(
        update={
            "planned_count": 50,
            "counts": Counts(
                complete=49, incomplete=0, invalid=1, failed=0, not_started=0
            ),
        }
    )

    def fake_inspection(_root: Path, *, planner_factory: object) -> Inspection:
        del planner_factory
        return Inspection(original.plan, report)

    monkeypatch.setattr(concurrency_sweep, "inspect_evidence", fake_inspection)
    run = json.loads((root / "run.json").read_bytes())
    run["cli_version"] = "codex-cli 0.166.0"
    (root / "run.json").write_text(json.dumps(run))
    stream = next(root.rglob("attempt-1.stdout"))
    events = [json.loads(line) for line in stream.read_bytes().splitlines()]
    events.insert(2, {"type": "error", "message": "Reconnecting... 1/5 (test)"})
    stream.write_bytes(b"".join(json.dumps(event).encode() + b"\n" for event in events))
    concurrency_sweep.check_block(
        root, frozen_manifest()["pairs"], ("/synthetic/codex", "codex-cli 0.166.0")
    )
    events.insert(
        3,
        {"type": "item.completed", "item": {"id": "tool", "type": "command_execution"}},
    )
    stream.write_bytes(b"".join(json.dumps(event).encode() + b"\n" for event in events))
    with pytest.raises(ValueError):
        concurrency_sweep.check_block(
            root, frozen_manifest()["pairs"], ("/synthetic/codex", "codex-cli 0.166.0")
        )
