# SPDX-License-Identifier: Apache-2.0
"""Prepare or, with future explicit authority, run the C concurrency sweep."""

import argparse
import asyncio
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import TypedDict, cast
from uuid import uuid4

from script.eval.evidence import create_evidence_store
from script.eval.evidence_status import EvidenceStatus
from script.eval.model import (
    DryRunReport,
    EstimateBasis,
    FrozenInputs,
    FrozenPlan,
    HarnessConfig,
    RunRecord,
    TokenEstimate,
)
from script.eval.options import parse_config
from script.eval.plan import PurePlanBuilder
from script.eval.runner.ports import CliBinding, CliBindingResolver
from script.eval.standalone import create_composition, run_owned
from script.eval.workspace import acquire_workspace, validate_workspace_selection
from script.reviewer_eval.report import inspect_evidence
from script.reviewer_eval.sweep_manifest import INPUT, MANIFEST, ROOT, generate
from script.reviewer_eval.transcript import extract_response


class Block(TypedDict):
    """One fixed schedule position."""

    repetition: int
    concurrency: int


class Manifest(TypedDict):
    """Public selected pairs and exact block schedule."""

    pairs: list[dict[str, object]]
    blocks: list[Block]


DIRECTORIES = tuple(
    str(INPUT / name) for name in ("c-shared", "c-rules", "c-functions")
)
INSTRUCTIONS = ROOT / "preparation/min.md"


class ByteQuarterEstimator:
    """Use the existing C byte/4 planning proxy without a tokenizer download."""

    def estimate(
        self, content: bytes, model: str, basis: EstimateBasis, /
    ) -> TokenEstimate:
        """Estimate supplied bytes with the declared C proxy.

        Returns:
            An approximate estimate, not an actual token count.
        """
        return TokenEstimate(
            model=model,
            token_count=(len(content) + 3) // 4,
            method="utf8-byte-quarter",
            library_version="1",
            tokenizer_version=None,
            basis=basis,
            compatibility="approximate",
            diagnostic="C byte/4 proxy; not a tokenizer or usage guarantee",
        )


class SweepPlanBuilder:
    """Select only the frozen pairs from ordinary composed C contexts."""

    def __init__(self, run_id: str, pairs: list[dict[str, object]]) -> None:
        self.run_id = run_id
        self.pairs = pairs

    def plan(self, inputs: FrozenInputs, config: HarnessConfig, /) -> FrozenPlan:
        """Recompose and validate the selected calls against the public manifest.

        Returns:
            The selected plan.

        Raises:
            ValueError: The selected pair or composed bytes differ.
        """
        if config.concurrency not in (1, 5, 10, 25) or config != configuration(
            config.concurrency, config.output_directory
        ):
            raise ValueError("sweep configuration drift")
        full = PurePlanBuilder(self.run_id).plan(inputs, config)
        calls = []
        for pair in self.pairs:
            rule = str(INPUT / "c-rules" / str(pair["rule_file"]))
            function = str(INPUT / "c-functions" / str(pair["function_file"]))
            matches = [
                call
                for call in full.calls
                if rule
                in (full.snapshots[i].repository_path for i in call.context_indices)
                and function
                in (full.snapshots[i].repository_path for i in call.context_indices)
            ]
            if len(matches) != 1:
                raise ValueError("selected pair absent or ambiguous")
            call = matches[0]
            if (
                call.prompt_sha256 != pair["prompt_sha256"]
                or len(call.prompt) != pair["prompt_bytes"]
            ):
                raise ValueError("selected prompt drift")
            calls.append(call.model_copy(update={"position": len(calls)}))
        if len(calls) != 50 or len({c.context_indices for c in calls}) != 50:
            raise ValueError("selection must contain 50 distinct pairs")
        return full.model_copy(update={"calls": tuple(calls)})


def configuration(concurrency: int, output: Path | None) -> HarnessConfig:
    """Build the fixed execution configuration.

    Returns:
        The fixed configuration for one block.
    """
    options = [part for path in DIRECTORIES for part in ("-d", path)]
    options += [
        "-i",
        str(INSTRUCTIONS),
        "-m",
        "gpt-6-luna",
        "-e",
        "high",
        "-c",
        str(concurrency),
        "--timeout-seconds",
        "300",
        "--cleanup-timeout-seconds",
        "10",
        "--output-limit-bytes",
        str(1024 * 1024),
        "--retry-limit",
        "0",
        "--capacity-retry-limit",
        "0",
        "--sandbox-mode",
        "read-only",
        "--quiet",
    ]
    options += ["-n"] if output is None else ["-o", str(output)]
    return parse_config(options)


def frozen_manifest() -> Manifest:
    """Require the exact algorithm output and every public input digest.

    Returns:
        The verified public manifest.

    Raises:
        ValueError: The manifest or inputs have drifted.
    """
    raw = MANIFEST.read_bytes()
    if raw != generate():
        raise ValueError("manifest or inputs drifted")
    return cast(Manifest, json.loads(raw))


async def prepare(pairs: list[dict[str, object]]) -> DryRunReport:
    """Estimate without resolving a CLI binding or constructing evidence.

    Returns:
        The selected plan and its offline estimates.
    """
    status = EvidenceStatus(create_evidence_store)
    composition = create_composition(status)
    result = await replace(
        composition,
        planner=SweepPlanBuilder("dry-run", pairs),
        estimator=ByteQuarterEstimator(),
    ).execute(configuration(1, None))
    assert isinstance(result, DryRunReport)
    return result


def estimates(report: DryRunReport, manifest: Manifest) -> int:
    """Print the fixed schedule and complete supplied-input estimates.

    Returns:
        The estimated supplied input tokens across the complete schedule.

    Raises:
        ValueError: A supplied-input estimate is unknown.
    """
    values = [
        (
            e.context.token_count,
            e.instructions_file.token_count if e.instructions_file else None,
        )
        for e in report.estimates
    ]
    if any(a is None or b is None for a, b in values):
        raise ValueError("complete token estimates are required")
    context = sum(a for a, _ in values if a is not None)
    instructions = sum(b for _, b in values if b is not None)
    total = context + instructions
    prompt_bytes = sum(len(c.prompt) for c in report.plan.calls)
    lines = [
        "50 pairs, 12 blocks, 600 calls and attempts; "
        f"prompt bytes/block: {prompt_bytes}"
    ]
    for index, pair in enumerate(manifest["pairs"]):
        lines.append(
            f"{index + 1:02}: {pair['rule_id']} {pair['file_id']} "
            f"{pair['function_name']} bin={pair['size_bin']}"
        )
    method = report.estimates[0].context
    lines.append(
        f"Estimator: {method.method} {method.library_version}, "
        f"{method.tokenizer_version}; {method.compatibility}; {method.diagnostic}"
    )
    for block in manifest["blocks"]:
        lines.append(
            f"block rep={block['repetition']} concurrency={block['concurrency']}: "
            f"50 calls; context={context}, instructions={instructions}, "
            f"total={total} tokens"
        )
    lines.extend([
        f"600-call supplied-input estimate: {total * 12} tokens; excludes "
        "automatic context, framing and output; not usage or cost",
        "300s/call + 10s cleanup; 1 MiB/attempt; retries=0; quota probes=0; "
        "600 MiB output before evidence overhead",
        "Serial capacity 51h 40m; 201 waves = 17h 18m 30s; both exclude overhead; "
        "actual subscription cost unknown",
    ])
    sys.stdout.write("\n".join(lines) + "\n")
    return total * 12


def head() -> str:
    """Return a clean checkout HEAD without changing Git state.

    Raises:
        ValueError: The checkout is dirty.
    """
    env = {
        name: value for name, value in os.environ.items() if not name.startswith("GIT_")
    }
    env.update({
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.fsmonitor",
        "GIT_CONFIG_VALUE_0": "false",
    })
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        capture_output=True,
        check=True,
        env=env,
        stdin=subprocess.DEVNULL,
        timeout=20,
    )
    if status.stdout:
        raise ValueError("checkout must be clean")
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        check=True,
        env=env,
        stdin=subprocess.DEVNULL,
        timeout=20,
        text=True,
    ).stdout.strip()


def cli() -> tuple[str, str]:
    """Verify the currently selected system CLI and its version.

    Returns:
        The absolute executable path and version.

    Raises:
        ValueError: The executable or required version is unavailable.
    """
    path = shutil.which("codex")
    if not path:
        raise ValueError("codex executable not found")
    path = str(Path(path).resolve(strict=True))
    result = subprocess.run(
        [path, "--version"],
        capture_output=True,
        check=True,
        stdin=subprocess.DEVNULL,
        timeout=5,
        text=True,
    )
    if result.stdout.strip() != "codex-cli 0.166.0":
        raise ValueError("requires codex-cli 0.166.0")
    return path, result.stdout.strip()


def host_conditions() -> dict[str, object]:
    """Capture locally observable host context without probing the provider.

    Returns:
        CPU and load observations and explicitly unknown external conditions.
    """
    try:
        load = os.getloadavg()
    except OSError:
        load = None
    return {
        "cpu_count": os.cpu_count(),
        "load_average": load,
        "network_conditions": "unknown",
        "provider_account_activity": "unknown",
        "cache_and_usage_observations": "unknown",
    }


def stored_bytes(root: Path) -> int:
    """Count retained regular evidence bytes without following symbolic links.

    Returns:
        The current logical evidence size in bytes.

    Raises:
        ValueError: The evidence tree contains a symbolic link.
    """
    total = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("symbolic link in evidence root")
        if path.is_file():
            total += path.stat().st_size
    return total


def fresh_output_path(path: Path) -> Path:
    """Resolve a fresh evidence destination outside the checkout.

    Returns:
        The destination under its resolved existing parent.

    Raises:
        ValueError: The destination is within the checkout.
        FileExistsError: The destination already exists.
    """
    output = path.parent.resolve(strict=True) / path.name
    if output.is_relative_to(Path.cwd().resolve()):
        raise ValueError("evidence root must be outside the checkout")
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"evidence root already exists: {output}")
    return output


class CheckedBinding:
    """Refuse a changed executable before evidence creation or dispatch."""

    def __init__(self, resolver: CliBindingResolver, expected: tuple[str, str]) -> None:
        self.resolver = resolver
        self.expected = expected

    def resolve(self, config: HarnessConfig, /) -> CliBinding:
        """Resolve and require the approved version and executable path.

        Returns:
            The verified binding.

        Raises:
            ValueError: The selected executable or version changed.
        """
        binding = self.resolver.resolve(config)
        if (str(binding.executable_path), binding.cli_version) != self.expected:
            raise ValueError("bound CLI changed")
        return binding


async def execute_block(
    config: HarnessConfig,
    status: EvidenceStatus,
    pairs: list[dict[str, object]],
    expected: tuple[str, str],
) -> DryRunReport | RunRecord:
    """Use the ordinary owned workspace and supervisor composition.

    Returns:
        The completed harness result.
    """
    launch_cwd = Path.cwd().resolve()
    resolved = validate_workspace_selection(config, launch_cwd)
    async with acquire_workspace(config, resolved) as workspace:
        composition = create_composition(status, workspace.cwd, launch_cwd, resolved)
        return await replace(
            composition,
            planner=SweepPlanBuilder(str(uuid4()), pairs),
            binding_resolver=CheckedBinding(composition.binding_resolver, expected),
        ).execute(config)


async def timed_block(
    config: HarnessConfig,
    status: EvidenceStatus,
    pairs: list[dict[str, object]],
    executable: tuple[str, str],
    deadline: float,
) -> int:
    """Cancel and settle the owned run when the authorized deadline expires.

    Returns:
        The owned run status, including cancellation.
    """
    async with asyncio.timeout(max(0.0, deadline - time.monotonic())):
        return await run_owned(
            config, status, lambda c, s: execute_block(c, s, pairs, executable)
        )


def check_block(
    output: Path, pairs: list[dict[str, object]], expected_cli: tuple[str, str]
) -> None:
    """Refuse unsafe, incomplete, unexpected or insufficient public evidence.

    Raises:
        ValueError: The evidence fails the block continuation rules.
    """
    inspection = inspect_evidence(
        output, planner_factory=lambda run_id: SweepPlanBuilder(run_id, pairs)
    )
    report = inspection.report
    if (
        inspection.plan is None
        or report.counts is None
        or report.evidence_state != "complete"
        or report.planned_count != 50
        or report.counts.complete < 49
    ):
        raise ValueError(
            "block evidence incomplete, invalid or below 49 valid responses"
        )
    run = RunRecord.model_validate_json((output / "run.json").read_bytes())
    if (run.codex_path, run.cli_version) != expected_cli:
        raise ValueError("bound CLI changed")
    for call in report.calls:
        for attempt in call.attempts:
            path = (
                output
                / "attempts"
                / f"position-{attempt.position}"
                / sha256(attempt.call_id.encode()).hexdigest()
                / f"attempt-{attempt.attempt_number}"
            )
            if path.with_suffix(".stderr").read_bytes().strip():
                raise ValueError("unexpected stderr; retained for review")
            extract_response(path.with_suffix(".stdout").read_bytes())


def positive(value: str) -> float:
    """Parse a finite positive authorization bound.

    Returns:
        The validated bound.

    Raises:
        argparse.ArgumentTypeError: The bound is not finite and positive.
    """
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError("bound must be finite and positive")
    return result


def parser() -> argparse.ArgumentParser:
    """Describe dry-run and future execution options.

    Returns:
        The argument parser.
    """
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--execute",
        action="store_true",
        help="execute only after separate explicit 600-call authorization",
    )
    p.add_argument(
        "--authorized-600-calls",
        action="store_true",
        help="assert that future execution authority has been granted",
    )
    p.add_argument("--output", type=Path, help="fresh external evidence root")
    p.add_argument("--token-planning-ceiling", type=positive)
    p.add_argument("--wall-seconds", type=positive)
    p.add_argument("--evidence-bytes", type=positive)
    return p


def run_block(
    runner: asyncio.Runner,
    config: HarnessConfig,
    pairs: list[dict[str, object]],
    executable: tuple[str, str],
    deadline: float,
) -> int:
    """Run one owned block and retain launcher output and timing.

    Returns:
        The settled process status.

    Raises:
        ValueError: The saved evidence fails continuation checks.
    """
    destination = config.output_directory
    assert destination is not None
    output = destination.parent
    name = destination.name
    status = EvidenceStatus(create_evidence_store)
    started = datetime.now(UTC).isoformat()
    tick = time.monotonic()
    try:
        with (
            (output / f"{name}.stdout").open("x") as stdout,
            (output / f"{name}.stderr").open("x") as stderr,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            code = runner.run(timed_block(config, status, pairs, executable, deadline))
    finally:
        ended = time.monotonic()
        (output / f"{name}.timing.json").write_text(
            json.dumps(
                {
                    "start_utc": started,
                    "end_utc": datetime.now(UTC).isoformat(),
                    "start_monotonic": tick,
                    "end_monotonic": ended,
                    "elapsed_seconds": ended - tick,
                    "host_conditions_after_block": host_conditions(),
                },
                indent=2,
            )
            + "\n"
        )
    if code != 0:
        return code
    if (output / f"{name}.stderr").read_bytes().strip():
        raise ValueError("unexpected launcher stderr; retained for review")
    check_block(destination, pairs, executable)
    return 0


def run_schedule(
    runner: asyncio.Runner,
    manifest: Manifest,
    output: Path,
    revision: str,
    executable: tuple[str, str],
    deadline: float,
    evidence_bytes: float,
) -> int:
    """Run each authorized block in fixed order, stopping on any failed guard.

    Returns:
        The first nonzero block status or zero after all blocks.

    Raises:
        ValueError: A pre-block guard or retained evidence check fails.
    """
    pairs = manifest["pairs"]
    for index, block in enumerate(manifest["blocks"]):
        remaining_output = (len(manifest["blocks"]) - index) * 50 * 1024 * 1024
        if (
            head() != revision
            or cli() != executable
            or frozen_manifest() != manifest
            or time.monotonic() >= deadline
        ):
            raise ValueError("pre-block drift or deadline")
        if (
            stored_bytes(output) + remaining_output > evidence_bytes
            or shutil.disk_usage(output).free < remaining_output
        ):
            raise ValueError("pre-block evidence or free storage ceiling")
        name = f"{index + 1:02}-rep{block['repetition']}-c{block['concurrency']}"
        destination = output / name
        config = configuration(block["concurrency"], destination)
        code = run_block(runner, config, pairs, executable, deadline)
        if code != 0:
            return code
        if stored_bytes(output) > evidence_bytes:
            raise ValueError("evidence ceiling exceeded; retained for review")
    return 0


def main() -> int:
    """Print preparation or run the separately authorized bounded schedule.

    Returns:
        The process status.

    Raises:
        ValueError: Execution authorization or prerequisites are insufficient.
    """
    args = parser().parse_args()
    invocation_start = time.monotonic()
    manifest = frozen_manifest()
    pairs = manifest["pairs"]
    with asyncio.Runner() as runner:
        report = runner.run(prepare(pairs))
        total = estimates(report, manifest)
        if not args.execute:
            return 0
        if (
            not args.authorized_600_calls
            or args.output is None
            or args.token_planning_ceiling is None
            or args.wall_seconds is None
            or args.evidence_bytes is None
        ):
            raise ValueError(
                "execution requires explicit authority and finite token, "
                "wall and evidence bounds"
            )
        if (
            args.token_planning_ceiling < total
            or args.wall_seconds <= 186000
            or args.evidence_bytes <= 600 * 1024 * 1024
        ):
            raise ValueError(
                "authorized bounds do not cover the planned capacity and overhead"
            )
        output = fresh_output_path(args.output)
        revision = head()
        executable = cli()
        if shutil.disk_usage(output.parent).free < args.evidence_bytes:
            raise ValueError("insufficient free evidence storage")
        output.mkdir(parents=False, exist_ok=False)
        (output / "manifest.json").write_bytes(MANIFEST.read_bytes())
        (output / "launcher.py").write_bytes(Path(__file__).read_bytes())
        (output / "launch.json").write_text(
            json.dumps(
                {
                    "head": revision,
                    "cli": executable,
                    "manifest_sha256": sha256(MANIFEST.read_bytes()).hexdigest(),
                    "launcher_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                    "arguments": sys.argv[1:],
                    "invocation_start_monotonic": invocation_start,
                    "deadline_monotonic": invocation_start + args.wall_seconds,
                    "prelaunch_utc": datetime.now(UTC).isoformat(),
                    "host_conditions": host_conditions(),
                },
                indent=2,
            )
            + "\n"
        )
        return run_schedule(
            runner,
            manifest,
            output,
            revision,
            executable,
            invocation_start + args.wall_seconds,
            args.evidence_bytes,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
