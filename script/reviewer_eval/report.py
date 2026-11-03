# SPDX-License-Identifier: Apache-2.0
"""Inspect saved harness evidence without reading the original checkout."""

from collections import Counter
from contextlib import ExitStack
from hashlib import sha256
import os
from pathlib import Path
import stat
from typing import Any

from script.eval.model import (
    AttemptRecord,
    CallRecord,
    FrozenInputs,
    FrozenPlan,
    PreparedEvidence,
    RunRecord,
)
from script.eval.plan import PurePlanBuilder
from script.eval.runner.adapters import CodexAttemptRequestBuilder
from script.eval.runner.coordinator.records import settings_digest
from script.eval.runner.policy import safe_process_cleanup
from script.eval.runner.ports import CliBinding
from script.reviewer_eval.context import review_context
from script.reviewer_eval.transcript import extract_response, parse_json
from script.reviewer_eval.validation import InvalidResponse, validate_response

STATES = ("complete", "incomplete", "invalid", "failed", "not_started")


class MissingBinding(ValueError):
    """The saved summary does not contain the executable binding."""


def _read(root: Path, relative: Path) -> bytes:
    """Read a regular file under root without traversing symbolic links.

    Returns:
        The file bytes.

    Raises:
        ValueError: The path is unsafe or is not a regular file.
    """
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe evidence path: {relative}")
    parts = relative.parts
    if not parts:
        raise ValueError("empty evidence path")
    with ExitStack() as stack:
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        stack.callback(os.close, directory)
        for part in parts[:-1]:
            directory = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
            )
            stack.callback(os.close, directory)
        descriptor = os.open(
            parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
        )
        stream = stack.enter_context(os.fdopen(descriptor, "rb"))
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError(f"evidence is not a regular file: {relative}")
        return stream.read()


def _load(root: Path, relative: Path, model: type[Any]) -> Any:
    raw = _read(root, relative)
    parse_json(raw)  # Reject duplicate keys before pydantic parses the bytes.
    return model.model_validate_json(raw)


def _plan(root: Path) -> FrozenPlan:
    plan: FrozenPlan = _load(root, Path("plan.json"), FrozenPlan)
    if any(sha256(s.content).hexdigest() != s.content_sha256 for s in plan.snapshots):
        raise ValueError("snapshot digest mismatch")
    instruction = plan.instructions_file
    if (
        instruction
        and sha256(instruction.content).hexdigest() != instruction.content_sha256
    ):
        raise ValueError("instruction digest mismatch")
    inputs = FrozenInputs(
        plan.repository_root, plan.head_commit, plan.snapshots, instruction
    )
    if PurePlanBuilder(plan.run_id).plan(inputs, plan.configuration) != plan:
        raise ValueError("plan matrix, prompt or boundary mismatch")
    if not plan.calls:
        raise ValueError("plan has no calls")
    for call in plan.calls:
        review_context(plan, call)
    return plan


def _call_error(
    root: Path, plan: FrozenPlan, run: RunRecord, call: CallRecord
) -> str | None:
    planned = plan.calls[call.position]
    snapshots = tuple(plan.snapshots[i] for i in planned.context_indices)
    expected = (
        plan.run_id,
        tuple(s.repository_path for s in snapshots),
        tuple(s.content_sha256 for s in snapshots),
        tuple(b.hex() for b in plan.boundary_bytes),
        planned.prompt_sha256,
        planned.model,
        planned.effort,
        settings_digest(run.effective_settings),
    )
    actual = (
        call.run_id,
        call.source_paths,
        call.source_sha256,
        call.boundary_bytes_hex,
        call.prompt_sha256,
        call.model,
        call.effort,
        call.effective_settings_sha256,
    )
    if actual != expected:
        return f"call {call.position} identity or settings mismatch"
    if tuple(a.attempt_number for a in call.attempts) != tuple(
        range(1, len(call.attempts) + 1)
    ):
        return f"call {call.position} attempt sequence mismatch"
    if call.state == "not_started" and call.attempts:
        return f"call {call.position} has attempts but is not started"
    return _bound_error(root, plan, run, call)


def _bound_error(
    root: Path, plan: FrozenPlan, run: RunRecord, call: CallRecord
) -> str | None:
    planned = plan.calls[call.position]
    if run.codex_path is None:
        raise MissingBinding("missing bound executable")
    binding = CliBinding(
        Path(run.codex_path),
        run.cli_version,
        run.runner_version,
        run.effective_settings,
        None,
    )
    staged = root / "instructions.bin" if plan.instructions_file else None
    prepared = PreparedEvidence(root, root / "plan.json", staged)
    effective = CodexAttemptRequestBuilder().build(
        plan, planned, binding, prepared, plan.configuration
    )
    if call.call_id != effective.call_id:
        return f"call {call.position} effective identity mismatch"
    request = effective.request
    for attempt in call.attempts:
        if (
            attempt.argv,
            attempt.cwd,
            attempt.timeout_seconds,
            attempt.cleanup_timeout_seconds,
            attempt.grace_seconds,
            attempt.output_limit_bytes,
        ) != (
            request.argv,
            str(request.cwd),
            request.timeout_seconds,
            request.cleanup_timeout_seconds,
            request.grace_seconds,
            request.output_limit_bytes,
        ):
            return f"call {call.position} request mismatch"
        if (attempt.run_id, attempt.call_id, attempt.position) != (
            plan.run_id,
            call.call_id,
            call.position,
        ):
            return f"call {call.position} attempt identity mismatch"
    return None


def _run_error(root: Path, plan: FrozenPlan, run: RunRecord) -> str | None:
    if (run.run_id, run.repository_root, run.head_commit) != (
        plan.run_id,
        str(plan.repository_root),
        plan.head_commit,
    ):
        return "run identity mismatch"
    if tuple(c.position for c in run.calls) != tuple(range(len(plan.calls))):
        return "run call matrix mismatch"
    if any(not c.call_id for c in run.calls):
        return "empty call identity"
    for call in run.calls:
        error = _call_error(root, plan, run, call)
        if error:
            return error
    return None


def _base(call: CallRecord, attempt: AttemptRecord) -> Path:
    identity = sha256(call.call_id.encode()).hexdigest()
    return (
        Path("attempts")
        / f"position-{call.position}"
        / identity
        / f"attempt-{attempt.attempt_number}"
    )


def _artifacts(
    root: Path, call: CallRecord, attempt: AttemptRecord
) -> tuple[bytes | None, set[Path]]:
    base = _base(call, attempt)
    metadata = base.with_suffix(".json")
    stored: AttemptRecord = _load(root, metadata, AttemptRecord)
    if stored != attempt:
        raise ValueError(f"attempt metadata mismatch: {metadata}")
    expected = {metadata}
    streams: list[bytes | None] = []
    for suffix, reference in (
        (".stdout", attempt.stdout_artifact),
        (".stderr", attempt.stderr_artifact),
    ):
        path = base.with_suffix(suffix)
        if reference is None:
            streams.append(None)
            continue
        if reference != str(root / path):
            raise ValueError(f"attempt stream path mismatch: {path}")
        expected.add(path)
        streams.append(_read(root, path))
    return streams[0], expected


def _inventory(root: Path) -> set[Path]:
    directory = root / "attempts"
    if not directory.exists() and not directory.is_symlink():
        return set()
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("attempts is not a regular directory")
    result: set[Path] = set()
    for current, dirs, files in os.walk(directory, followlinks=False):
        for name in (*dirs, *files):
            path = Path(current) / name
            if path.is_symlink():
                raise ValueError(f"symbolic link in attempts: {path}")
        result.update((Path(current) / name).relative_to(root) for name in files)
    return result


def _result(plan: FrozenPlan, call: CallRecord, stdout: bytes | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "position": call.position,
        "call_id": call.call_id,
        "state": "failed",
        "diagnostic": None,
        "attempts": [a.model_dump(mode="json") for a in call.attempts],
        "selected_attempt": None,
        "findings": [],
    }
    if not call.attempts:
        result["state"] = "not_started" if call.state == "not_started" else "incomplete"
        result["diagnostic"] = (
            None if call.state == "not_started" else "no durable attempt"
        )
        return result
    attempt = call.attempts[-1]
    if call.state == "running":
        result.update(state="incomplete", diagnostic="call is still running")
        return result
    if (
        call.state != "complete"
        or attempt.control_flow != "returned"
        or attempt.outcome_kind != "completed"
        or attempt.exit_status != 0
        or not safe_process_cleanup(attempt)
    ):
        result["diagnostic"] = "terminal call or attempt did not complete successfully"
        return result
    if stdout is None:
        result.update(state="incomplete", diagnostic="terminal stdout is unavailable")
        return result
    try:
        thread_id, response = extract_response(stdout)
        rules, sources = review_context(plan, plan.calls[call.position])
        validated = validate_response(response, allowed_rules=rules, sources=sources)
    except ValueError as exc:
        result.update(state="invalid", diagnostic=str(exc))
        return result
    result["thread_id"] = thread_id
    result["selected_attempt"] = attempt.attempt_number
    if isinstance(validated, InvalidResponse):
        result.update(state="invalid", diagnostic=validated.diagnostic)
    else:
        result.update(
            state="complete" if validated.complete else "incomplete",
            diagnostic=None if validated.complete else "reviewer reported incomplete",
            findings=[f.model_dump(mode="json") for f in validated.findings],
        )
    return result


def _report(
    plan: FrozenPlan | None,
    state: str,
    diagnostic: str | None,
    calls: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = Counter(call["state"] for call in calls)
    return {
        "version": 1,
        "evidence_state": state,
        "diagnostic": diagnostic,
        "planned_count": len(plan.calls) if plan else None,
        "counts": {key: counts[key] for key in STATES} if plan else None,
        "calls": calls,
        "scope": (
            "Internal artifact consistency and correspondence to frozen source "
            "bytes only; not authenticated lineage, safe-read verification, "
            "semantic truth, or quality readiness."
        ),
    }


def _uniform(plan: FrozenPlan, state: str, diagnostic: str) -> list[dict[str, Any]]:
    return [
        {
            "position": c.position,
            "call_id": None,
            "state": state,
            "diagnostic": diagnostic,
            "attempts": [],
            "selected_attempt": None,
            "findings": [],
        }
        for c in plan.calls
    ]


def _inspect_records(
    root: Path, plan: FrozenPlan, run: RunRecord
) -> list[dict[str, Any]]:
    error = _run_error(root, plan, run)
    if error:
        raise ValueError(error)
    if (
        plan.instructions_file
        and _read(root, Path("instructions.bin")) != plan.instructions_file.content
    ):
        raise ValueError("staged instructions do not match frozen bytes")
    expected: set[Path] = set()
    results = []
    for call in run.calls:
        stdout = None
        for attempt in call.attempts:
            stdout, paths = _artifacts(root, call, attempt)
            expected.update(paths)
        results.append(_result(plan, call, stdout))
    thread_ids = [r["thread_id"] for r in results if "thread_id" in r]
    if len(thread_ids) != len(set(thread_ids)):
        raise ValueError("completed calls reuse a thread identity")
    if _inventory(root) != expected:
        raise ValueError("extra, missing, or foreign attempt artifacts")
    return results


def _retained(root: Path, calls: list[dict[str, Any]]) -> None:
    """Attach individually readable attempts without asserting their identity."""
    try:
        paths = sorted(_inventory(root))
    except OSError, ValueError:
        return
    for path in paths:
        if path.suffix != ".json":
            continue
        try:
            attempt: AttemptRecord = _load(root, path, AttemptRecord)
        except OSError, ValueError:
            continue
        if attempt.position < len(calls):
            calls[attempt.position]["attempts"].append(attempt.model_dump(mode="json"))


def _uniform_with_retained(
    root: Path,
    plan: FrozenPlan,
    state: str,
    diagnostic: str,
    run: RunRecord | None = None,
) -> list[dict[str, Any]]:
    calls = _uniform(plan, state, diagnostic)
    if run is None:
        _retained(root, calls)
    else:
        for call in run.calls:
            if call.position < len(calls):
                calls[call.position]["attempts"].extend(
                    attempt.model_dump(mode="json") for attempt in call.attempts
                )
    return calls


def inspect_run(run_root: Path) -> dict[str, Any]:
    """Inspect one original run directory without reading its repository root.

    Returns:
        Deterministic accounting and retained validation observations.
    """
    root = run_root.resolve(strict=True)
    try:
        plan = _plan(root)
    except (OSError, ValueError, IndexError) as exc:
        return _report(None, "invalid", f"invalid plan: {exc}", [])
    try:
        run: RunRecord = _load(root, Path("run.json"), RunRecord)
    except FileNotFoundError:
        message = "run summary missing"
        return _report(
            plan,
            "incomplete",
            message,
            _uniform_with_retained(root, plan, "incomplete", message),
        )
    except (OSError, ValueError) as exc:
        message = f"invalid run: {exc}"
        return _report(
            plan,
            "invalid",
            message,
            _uniform_with_retained(root, plan, "invalid", message),
        )
    try:
        results = _inspect_records(root, plan, run)
    except (FileNotFoundError, MissingBinding) as exc:
        message = f"missing evidence: {exc}"
        return _report(
            plan,
            "incomplete",
            message,
            _uniform_with_retained(root, plan, "incomplete", message, run),
        )
    except (OSError, ValueError, IndexError) as exc:
        message = str(exc)
        return _report(
            plan,
            "invalid",
            message,
            _uniform_with_retained(root, plan, "invalid", message, run),
        )
    return _report(plan, run.state, None, results)
