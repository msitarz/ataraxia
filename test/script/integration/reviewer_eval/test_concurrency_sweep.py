# SPDX-License-Identifier: Apache-2.0
"""Verify the prospective sweep using public inputs and synthetic evidence."""

import asyncio
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import time

import pytest

from script.eval.evidence import create_evidence_store
from script.eval.evidence_status import EvidenceStatus
from script.eval.inputs import GitRepositoryReader
from script.eval.model import (
    DirectoryOption,
    DryRunReport,
    FrozenInputs,
    FrozenPlan,
    HarnessConfig,
    InstructionsSnapshot,
    RunRecord,
    SourceSnapshot,
)
from script.eval.plan import PurePlanBuilder
from script.eval.runner.adapters import (
    CodexAttemptRequestBuilder,
    CodexCliBindingResolver,
)
from script.eval.runner.adapters.codex import requested_settings
from script.eval.runner.ports import CliBinding
from script.reviewer_eval import concurrency_sweep as sweep
from script.reviewer_eval.report import inspect_evidence, inspect_run
from script.reviewer_eval.sweep_manifest import MANIFEST, Pair, generate
from test.script.integration.reviewer_eval.sweep_support import saved_sweep


def public_inputs(config: HarnessConfig) -> FrozenInputs:
    """Build public snapshots directly for an offline plan."""
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


def selected_plan(output: Path) -> tuple[FrozenPlan, list[Pair]]:
    """Build the sweep plan for synthetic saved evidence."""
    config = sweep.configuration(1, output)
    pairs = sweep.frozen_manifest()["pairs"]
    return sweep.SweepPlanBuilder("run", pairs).plan(
        public_inputs(config), config
    ), pairs


def test_selection_matches_original_composed_prompts() -> None:
    # Given
    config = sweep.configuration(1, None)
    inputs = public_inputs(config)
    pairs = sweep.frozen_manifest()["pairs"]
    full = PurePlanBuilder("run").plan(inputs, config)

    # When
    selected = sweep.SweepPlanBuilder("run", pairs).plan(inputs, config)

    # Then
    by_context = {call.context_indices: call for call in full.calls}
    assert len(full.calls) == 186
    assert len(selected.calls) == 50
    assert all(
        call.prompt == by_context[call.context_indices].prompt
        for call in selected.calls
    )
    assert [call.position for call in selected.calls] == list(range(50))


def test_changed_prompt_digest_is_refused() -> None:
    # Given
    config = sweep.configuration(1, None)
    pairs = sweep.frozen_manifest()["pairs"]
    altered = pairs.copy()
    altered[0] = pairs[0].copy()
    altered[0]["prompt_sha256"] = "0" * 64

    # When
    with pytest.raises(ValueError, match="prompt drift"):
        sweep.SweepPlanBuilder("run", altered).plan(public_inputs(config), config)

    # Then
    assert len(altered) == 50


def test_changed_effort_is_refused() -> None:
    # Given
    config = sweep.configuration(1, None)
    pairs = sweep.frozen_manifest()["pairs"]

    # When
    with pytest.raises(ValueError, match="configuration drift"):
        sweep.SweepPlanBuilder("run", pairs).plan(
            public_inputs(config), config.model_copy(update={"efforts": ("low",)})
        )

    # Then
    assert config.efforts == ("high",)


async def test_saved_reader_requires_explicit_selection(tmp_path: Path) -> None:
    # Given
    output = tmp_path / "evidence"
    plan, pairs = selected_plan(output)
    await create_evidence_store().create(output, plan)

    # When
    default = inspect_run(output)
    selected = inspect_evidence(
        output, planner_factory=lambda run_id: sweep.SweepPlanBuilder(run_id, pairs)
    )

    # Then
    assert default.evidence_state == "invalid"
    assert selected.plan == plan


async def test_saved_reader_rejects_changed_call_order(tmp_path: Path) -> None:
    # Given
    output = tmp_path / "evidence"
    plan, pairs = selected_plan(output)
    await create_evidence_store().create(output, plan)
    plan_path = output / "plan.json"
    tampered = json.loads(plan_path.read_bytes())
    tampered["calls"][0], tampered["calls"][1] = (
        tampered["calls"][1],
        tampered["calls"][0],
    )
    plan_path.write_text(json.dumps(tampered))

    # When
    inspection = inspect_evidence(
        output, planner_factory=lambda run_id: sweep.SweepPlanBuilder(run_id, pairs)
    )

    # Then
    assert inspection.plan is None


async def test_dry_run_has_no_cli_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given
    content = sweep.INSTRUCTIONS.read_bytes()

    def freeze(_self: GitRepositoryReader, config: HarnessConfig) -> FrozenInputs:
        return replace(
            public_inputs(config),
            instructions_file=InstructionsSnapshot(
                repository_path=str(sweep.INSTRUCTIONS),
                commit_blob_sha="0" * 40,
                content_sha256=sha256(content).hexdigest(),
                content=content,
            ),
        )

    def refuse(_self: CodexCliBindingResolver, _config: HarnessConfig) -> CliBinding:
        raise AssertionError("dry run resolved a CLI binding")

    monkeypatch.setattr(GitRepositoryReader, "freeze", freeze)
    monkeypatch.setattr(CodexCliBindingResolver, "resolve", refuse)

    # When
    report = await sweep.prepare(sweep.frozen_manifest()["pairs"])

    # Then
    assert report.scheduled_call_count == 50
    assert all(estimate.instructions_file is not None for estimate in report.estimates)


async def test_request_uses_empty_stdin_and_fixed_bounds(tmp_path: Path) -> None:
    # Given
    output = tmp_path / "evidence"
    config = sweep.configuration(25, output)
    plan = sweep.SweepPlanBuilder("run", sweep.frozen_manifest()["pairs"]).plan(
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

    # When
    request = (
        CodexAttemptRequestBuilder(invocation_cwd=tmp_path)
        .build(plan, plan.calls[0], binding, evidence, config)
        .request
    )

    # Then
    assert request.stdin == "devnull"
    assert (
        request.timeout_seconds,
        request.cleanup_timeout_seconds,
        request.output_limit_bytes,
    ) == (300, 10, 1024 * 1024)
    assert config.retry_limit == config.capacity_retry_limit == 0
    assert not config.quota_wait_enabled


async def test_deadline_waits_for_cancellation_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    cleaned = asyncio.Event()

    async def blocked(
        _config: HarnessConfig,
        _status: EvidenceStatus,
        _pairs: list[Pair],
        _expected: tuple[str, str],
    ) -> DryRunReport | RunRecord:
        try:
            await asyncio.Event().wait()
        finally:
            cleaned.set()
        raise AssertionError("unreachable")

    monkeypatch.setattr(sweep, "execute_block", blocked)
    status = EvidenceStatus(create_evidence_store)

    # When
    code = await sweep.timed_block(
        sweep.configuration(1, tmp_path / "block"),
        status,
        [],
        ("fake", "version"),
        time.monotonic() + 0.05,
    )

    # Then
    assert code == 130
    assert cleaned.is_set()


def test_frozen_manifest_has_predeclared_schedule() -> None:
    # Given
    raw = MANIFEST.read_bytes()

    # When
    manifest = sweep.frozen_manifest()

    # Then
    assert raw == generate()
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


def test_manifest_drift_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    changed = tmp_path / "manifest.json"
    changed.write_bytes(MANIFEST.read_bytes() + b" ")
    monkeypatch.setattr(sweep, "MANIFEST", changed)

    # When
    with pytest.raises(ValueError, match="drifted"):
        sweep.frozen_manifest()

    # Then
    assert changed.read_bytes().endswith(b" ")


def test_existing_evidence_root_is_refused(tmp_path: Path) -> None:
    # Given
    existing = tmp_path / "existing"
    existing.mkdir()

    # When
    with pytest.raises(FileExistsError):
        sweep.fresh_output_path(existing)

    # Then
    assert list(existing.iterdir()) == []


def test_scheduled_wave_capacity_allows_the_disclosed_overhead() -> None:
    # Given
    evidence = 600 * 1024 * 1024 + 1

    # When
    result = sweep.require_planning_bounds(100, 100, 62910, evidence)

    # Then
    assert result is None


def test_wall_bound_below_wave_capacity_and_overhead_is_refused() -> None:
    # Given
    evidence = 600 * 1024 * 1024 + 1

    # When
    with pytest.raises(ValueError, match="planned capacity"):
        sweep.require_planning_bounds(100, 100, 62909, evidence)

    # Then
    assert evidence > 600 * 1024 * 1024


@pytest.mark.parametrize(
    "status", [1, 3, 130], ids=["failure", "incomplete", "cancelled"]
)
def test_nonzero_block_stops_and_keeps_timing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    # Given
    manifest = sweep.frozen_manifest()
    monkeypatch.setattr(sweep, "frozen_manifest", lambda: manifest)
    monkeypatch.setattr(sweep, "head", lambda: "head")
    monkeypatch.setattr(sweep, "cli", lambda: ("/fake/codex", "version"))
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

    monkeypatch.setattr(sweep, "timed_block", fake_block)

    # When
    with asyncio.Runner() as runner:
        result = sweep.run_schedule(
            runner,
            manifest,
            tmp_path,
            "head",
            ("/fake/codex", "version"),
            time.monotonic() + 10,
            1024 * 1024 * 1024,
        )

    # Then
    assert result == status
    assert starts == [1]
    timing = json.loads((tmp_path / "01-rep1-c1.timing.json").read_bytes())
    assert timing["end_monotonic"] >= timing["start_monotonic"]
    assert timing["elapsed_seconds"] >= 0


async def test_49_valid_with_known_stderr_and_transport_can_continue(
    tmp_path: Path,
) -> None:
    # Given
    root = tmp_path / "run"
    plan, pairs = selected_plan(root)
    await saved_sweep(root, plan)

    # When
    sweep.check_block(root, pairs, ("/synthetic/codex", "codex-cli 0.166.0"))

    # Then
    stderr = list(root.rglob("attempt-1.stderr"))
    assert len(stderr) == 50
    assert {path.read_bytes() for path in stderr} == {sweep.BENIGN_STDERR}


async def test_48_valid_stops_sweep(tmp_path: Path) -> None:
    # Given
    root = tmp_path / "run"
    plan, pairs = selected_plan(root)
    await saved_sweep(root, plan, invalid=2)

    # When
    with pytest.raises(ValueError, match="below 49"):
        sweep.check_block(root, pairs, ("/synthetic/codex", "codex-cli 0.166.0"))

    # Then
    assert (root / "run.json").exists()


async def test_unknown_stderr_stops_sweep(tmp_path: Path) -> None:
    # Given
    root = tmp_path / "run"
    plan, pairs = selected_plan(root)
    await saved_sweep(root, plan, stderr=sweep.BENIGN_STDERR + b"router warning\n")

    # When
    with pytest.raises(ValueError, match="unexpected stderr"):
        sweep.check_block(root, pairs, ("/synthetic/codex", "codex-cli 0.166.0"))

    # Then
    assert (root / "run.json").exists()


async def test_tool_activity_stops_sweep(tmp_path: Path) -> None:
    # Given
    root = tmp_path / "run"
    plan, pairs = selected_plan(root)
    await saved_sweep(root, plan, tool=True)

    # When
    with pytest.raises(ValueError, match="invalid completed item content"):
        sweep.check_block(root, pairs, ("/synthetic/codex", "codex-cli 0.166.0"))

    # Then
    assert (root / "run.json").exists()
