# SPDX-License-Identifier: Apache-2.0
"""Inspect saved harness evidence without reading the original checkout."""

from collections import Counter
from contextlib import ExitStack
from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import stat
import tomllib
from typing import Literal

from pydantic import BaseModel, ConfigDict

from script.eval.model import (
    AttemptRecord,
    CallRecord,
    FrozenInputs,
    FrozenPlan,
    PreparedEvidence,
    RunRecord,
    SettingValue,
)
from script.eval.plan import PurePlanBuilder
from script.eval.runner.adapters import CodexAttemptRequestBuilder
from script.eval.runner.adapters.codex import (
    CONTROL_PROFILE,
    INVOCATION_PROFILE,
    PROFILE_DIGEST,
    PROFILE_SETTING,
)
from script.eval.runner.coordinator.records import settings_digest
from script.eval.runner.policy import safe_process_cleanup
from script.eval.runner.ports import CliBinding
from script.reviewer_eval.context import ResponseFormat, response_format, review_context
from script.reviewer_eval.transcript import extract_response, parse_json
from script.reviewer_eval.validation import (
    Assessment,
    Finding,
    InvalidResponse,
    PublicPair,
    ValidatedAssessments,
    ValidatedResponse,
    validate_assessments,
    validate_response,
)

type Outcome = Literal["complete", "incomplete", "invalid", "failed", "not_started"]
type EvidenceState = Literal["complete", "incomplete", "invalid"]


class CallOutcome(BaseModel):
    """One planned call and its retained evidence."""

    model_config = ConfigDict(frozen=True)
    position: int
    model: str
    effort: str
    call_id: str | None = None
    state: Outcome
    diagnostic: str | None = None
    attempts: tuple[AttemptRecord, ...] = ()
    selected_attempt: int | None = None
    response_format: ResponseFormat | None = None
    findings: tuple[Finding, ...] = ()
    assessments: tuple[Assessment, ...] = ()
    missing_pairs: tuple[PublicPair, ...] = ()
    thread_id: str | None = None


class Counts(BaseModel):
    """Disjoint counts for the known planned inventory."""

    model_config = ConfigDict(frozen=True)
    complete: int
    incomplete: int
    invalid: int
    failed: int
    not_started: int


class Report(BaseModel):
    """Deterministic results based on internally consistent retained artifacts."""

    model_config = ConfigDict(frozen=True)
    version: Literal[2] = 2
    evidence_state: EvidenceState
    diagnostic: str | None
    run_id: str | None
    head_commit: str | None
    planned_count: int | None
    counts: Counts | None
    calls: tuple[CallOutcome, ...]
    scope: str = (
        "Internal artifact consistency and correspondence to frozen source "
        "bytes only; not authenticated lineage, safe-read verification, "
        "semantic truth, or quality readiness."
    )


class MissingBinding(ValueError):
    """The saved summary does not contain the executable binding."""


@dataclass(frozen=True)
class Inspection:
    """The validated frozen plan and observations from one inspection."""

    plan: FrozenPlan | None
    report: Report


def inspect_run(run_root: Path) -> Report:
    """Inspect one original run directory without reading its repository root.

    Returns:
        Deterministic accounting and retained validation observations.
    """
    return inspect_evidence(run_root).report


def inspect_evidence(run_root: Path) -> Inspection:
    """Inspect a run and retain the exact validated plan used for its report.

    Returns:
        The plan, if valid, and its inspection report.
    """
    root = run_root.resolve(strict=True)
    try:
        plan = _plan(root)
    except (OSError, ValueError, IndexError) as exc:
        return Inspection(None, _report(None, "invalid", f"invalid plan: {exc}", []))
    return Inspection(plan, _inspect_plan(root, plan))


def _inspect_plan(root: Path, plan: FrozenPlan) -> Report:
    """Inspect saved results against the already validated plan.

    Returns:
        The retained evidence report.
    """
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
    if run.codex_path is None:
        message = "missing bound executable"
        results = [
            result
            if result.state == "not_started"
            else result.model_copy(
                update={
                    "state": "incomplete",
                    "diagnostic": message,
                    "selected_attempt": None,
                    "findings": (),
                }
            )
            for result in results
        ]
        return _report(plan, "incomplete", message, results)
    return _report(plan, run.state, None, results)


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


def _load[T: BaseModel](root: Path, relative: Path, model: type[T]) -> T:
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
        response_format(plan, call)
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
    error = _history_error(plan, call)
    if error:
        return error
    if run.codex_path is None:
        return None
    return _bound_error(root, plan, run, call)


def _history_error(plan: FrozenPlan, call: CallRecord) -> str | None:
    for attempt in call.attempts:
        if (attempt.run_id, attempt.call_id, attempt.position) != (
            plan.run_id,
            call.call_id,
            call.position,
        ):
            return f"call {call.position} attempt identity mismatch"
    for attempt in call.attempts[:-1]:
        if not safe_process_cleanup(attempt):
            return f"call {call.position} continued after unsafe cleanup"
        if (
            attempt.control_flow == "returned"
            and attempt.outcome_kind == "completed"
            and attempt.exit_status == 0
        ):
            return f"call {call.position} continued after successful attempt"
    return None


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
    try:
        staged = _recorded_instructions(root, plan, call)
        cwd = _recorded_cwd(root, plan, run, call)
    except ValueError as error:
        return str(error)
    prepared = PreparedEvidence(root, root / "plan.json", staged)
    try:
        effective = CodexAttemptRequestBuilder(invocation_cwd=cwd).build(
            plan, planned, binding, prepared, plan.configuration
        )
    except ValueError as error:
        return str(error)
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


def _recorded_instructions(
    root: Path, plan: FrozenPlan, call: CallRecord
) -> Path | None:
    """Validate the recorded staged path without opening its original location.

    Returns:
        The recorded path, or None when instructions are absent.

    Raises:
        ValueError: The recorded path cannot match the frozen output location.
    """
    if plan.instructions_file is None:
        return None
    if not call.attempts:
        return root / "instructions.bin"
    argv = call.attempts[0].argv
    values = [
        argv[i + 1]
        for i, arg in enumerate(argv[:-1])
        if arg == "-c" and argv[i + 1].startswith("model_instructions_file=")
    ]
    try:
        staged = Path(tomllib.loads(values[0])["model_instructions_file"])
    except (IndexError, KeyError, TypeError, ValueError) as error:
        raise ValueError(f"call {call.position} invalid staged instructions") from error
    output = plan.configuration.output_directory
    assert output is not None
    valid_output = (
        staged.parent == output
        if output.is_absolute()
        else staged.parent.parts[-len(output.parts) :] == output.parts
    )
    if (
        not staged.is_absolute()
        or staged.name != "instructions.bin"
        or not valid_output
    ):
        raise ValueError(f"call {call.position} invalid staged instructions")
    return staged


def _recorded_cwd(
    root: Path, plan: FrozenPlan, run: RunRecord, call: CallRecord
) -> Path | None:
    """Select the recorded profile and validate its physical cwd policy.

    Returns:
        The recorded v2 cwd, a placeholder for an unstarted call, or None for v1.

    Raises:
        ValueError: The profile or recorded cwd is invalid.
    """
    settings = dict(run.effective_settings)
    profile = settings.get(PROFILE_SETTING)
    if profile is None:
        if "invocation_profile_sha256" in settings:
            raise ValueError("incomplete invocation profile")
        return None
    if profile == CONTROL_PROFILE:
        return _recorded_control_cwd(root, plan, settings, call)
    if (
        profile != INVOCATION_PROFILE
        or settings.get("invocation_profile_sha256") != PROFILE_DIGEST
    ):
        raise ValueError("unsupported invocation profile")
    if not call.attempts:
        return Path("/ataraxia-unused/empty")
    cwd = Path(call.attempts[0].cwd)
    if (
        not cwd.is_absolute()
        or cwd.name != "empty"
        or not cwd.parent.name.startswith("ataraxia-eval-")
        or cwd != Path(os.path.normpath(cwd))
    ):
        raise ValueError(f"call {call.position} invalid invocation cwd")
    if cwd.is_relative_to(plan.repository_root) or cwd.is_relative_to(root):
        raise ValueError(f"call {call.position} invalid invocation cwd")
    return cwd


def _recorded_control_cwd(
    root: Path, plan: FrozenPlan, settings: dict[str, SettingValue], call: CallRecord
) -> Path:
    """Reconstruct the recorded workspace without accessing its old location.

    Returns:
        The retained or placeholder workspace path.

    Raises:
        ValueError: Workspace metadata is invalid.
    """
    identity = settings.get("requested_workspace_identity")
    if plan.configuration.working_directory is not None:
        if not isinstance(identity, str):
            raise ValueError("missing workspace provenance")
        cwd = Path(identity)
    else:
        cwd = _recorded_owned_cwd(root, plan, call)
    if not cwd.is_absolute() or cwd != Path(os.path.normpath(cwd)):
        raise ValueError(f"call {call.position} invalid invocation cwd")
    return cwd


def _recorded_owned_cwd(root: Path, plan: FrozenPlan, call: CallRecord) -> Path:
    """Validate an owned physical path or provide an unstarted placeholder.

    Returns:
        The retained or placeholder path.

    Raises:
        ValueError: The recorded owned path is invalid.
    """
    if not call.attempts:
        return Path("/ataraxia-unused/empty")
    cwd = Path(call.attempts[0].cwd)
    if (
        cwd.name != "empty"
        or not cwd.parent.name.startswith("ataraxia-eval-")
        or cwd.is_relative_to(plan.repository_root)
        or cwd.is_relative_to(root)
    ):
        raise ValueError(f"call {call.position} invalid invocation cwd")
    return cwd


def _settings_error(run: RunRecord) -> str | None:
    """Check unique settings and the single run-owned v2 working directory.

    Returns:
        A diagnostic when inconsistent, otherwise None.
    """
    keys = [key for key, _ in run.effective_settings]
    if len(keys) != len(set(keys)):
        return "duplicate effective settings"
    if dict(run.effective_settings).get(PROFILE_SETTING) in (
        INVOCATION_PROFILE,
        CONTROL_PROFILE,
    ):
        cwds = {attempt.cwd for call in run.calls for attempt in call.attempts}
        if len(cwds) > 1:
            return "inconsistent invocation cwd"
    return None


def _run_error(root: Path, plan: FrozenPlan, run: RunRecord) -> str | None:
    if error := _settings_error(run):
        return error
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
    root: Path, plan: FrozenPlan, call: CallRecord, attempt: AttemptRecord
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
        recorded = Path(reference)
        output = plan.configuration.output_directory
        assert output is not None
        suffix_path = output / path
        if not recorded.is_absolute() or (
            recorded != suffix_path
            if output.is_absolute()
            else recorded.parts[-len(suffix_path.parts) :] != suffix_path.parts
        ):
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


def _result(plan: FrozenPlan, call: CallRecord, stdout: bytes | None) -> CallOutcome:
    planned = plan.calls[call.position]
    result = CallOutcome(
        position=call.position,
        model=planned.model,
        effort=planned.effort,
        call_id=call.call_id,
        state="failed",
        attempts=call.attempts,
        response_format=response_format(plan, planned),
    )
    if not call.attempts:
        return result.model_copy(
            update={
                "state": "not_started" if call.state == "not_started" else "incomplete",
                "diagnostic": None
                if call.state == "not_started"
                else "no durable attempt",
            }
        )
    attempt = call.attempts[-1]
    if call.state == "running":
        return result.model_copy(
            update={"state": "incomplete", "diagnostic": "call is still running"}
        )
    if (
        call.state != "complete"
        or attempt.control_flow != "returned"
        or attempt.outcome_kind != "completed"
        or attempt.exit_status != 0
        or not safe_process_cleanup(attempt)
    ):
        return result.model_copy(
            update={
                "diagnostic": "terminal call or attempt did not complete successfully"
            }
        )
    if stdout is None:
        return result.model_copy(
            update={
                "state": "incomplete",
                "diagnostic": "terminal stdout is unavailable",
            }
        )
    try:
        thread_id, response = extract_response(stdout)
        rules, sources = review_context(plan, planned)
    except ValueError as exc:
        return result.model_copy(update={"state": "invalid", "diagnostic": str(exc)})
    if result.response_format == "findings-v1":
        validated = validate_response(response, allowed_rules=rules, sources=sources)
    else:
        validated = validate_assessments(response, allowed_rules=rules, sources=sources)
    if isinstance(validated, InvalidResponse):
        return result.model_copy(
            update={
                "state": "invalid",
                "diagnostic": validated.diagnostic,
                "thread_id": thread_id,
                "selected_attempt": attempt.attempt_number,
            }
        )
    if result.response_format == "function-assessments-v2":
        assert isinstance(validated, ValidatedAssessments)
        return result.model_copy(
            update={
                "state": "complete" if validated.complete else "incomplete",
                "diagnostic": None if validated.complete else "missing public pairs",
                "assessments": validated.assessments,
                "missing_pairs": validated.missing,
                "thread_id": thread_id,
                "selected_attempt": attempt.attempt_number,
            }
        )
    assert isinstance(validated, ValidatedResponse)
    return result.model_copy(
        update={
            "state": "complete" if validated.complete else "incomplete",
            "diagnostic": None
            if validated.complete
            else "reviewer reported incomplete",
            "findings": validated.findings,
            "thread_id": thread_id,
            "selected_attempt": attempt.attempt_number,
        }
    )


def _report(
    plan: FrozenPlan | None,
    state: EvidenceState,
    diagnostic: str | None,
    calls: list[CallOutcome],
) -> Report:
    counts = Counter(call.state for call in calls)
    return Report(
        evidence_state=state,
        diagnostic=diagnostic,
        run_id=plan.run_id if plan else None,
        head_commit=plan.head_commit if plan else None,
        planned_count=len(plan.calls) if plan else None,
        counts=Counts(
            complete=counts["complete"],
            incomplete=counts["incomplete"],
            invalid=counts["invalid"],
            failed=counts["failed"],
            not_started=counts["not_started"],
        )
        if plan
        else None,
        calls=tuple(calls),
    )


def _uniform(plan: FrozenPlan, state: Outcome, diagnostic: str) -> list[CallOutcome]:
    return [
        CallOutcome(
            position=c.position,
            model=c.model,
            effort=c.effort,
            state=state,
            diagnostic=diagnostic,
            response_format=response_format(plan, c),
        )
        for c in plan.calls
    ]


def _inspect_records(root: Path, plan: FrozenPlan, run: RunRecord) -> list[CallOutcome]:
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
            stdout, paths = _artifacts(root, plan, call, attempt)
            expected.update(paths)
        results.append(
            _result(plan, call, stdout)
            if run.codex_path is not None or not call.attempts
            else CallOutcome(
                position=call.position,
                model=plan.calls[call.position].model,
                effort=plan.calls[call.position].effort,
                call_id=call.call_id,
                state="incomplete",
                diagnostic="missing bound executable",
                response_format=response_format(plan, plan.calls[call.position]),
                attempts=call.attempts,
            )
        )
    thread_ids = [r.thread_id for r in results if r.thread_id is not None]
    if len(thread_ids) != len(set(thread_ids)):
        raise ValueError("completed calls reuse a thread identity")
    if _inventory(root) != expected:
        raise ValueError("extra, missing, or foreign attempt artifacts")
    return results


def _retained(root: Path, calls: list[CallOutcome]) -> None:
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
            previous = calls[attempt.position]
            calls[attempt.position] = previous.model_copy(
                update={"attempts": (*previous.attempts, attempt)}
            )


def _uniform_with_retained(
    root: Path,
    plan: FrozenPlan,
    state: Outcome,
    diagnostic: str,
    run: RunRecord | None = None,
) -> list[CallOutcome]:
    calls = _uniform(plan, state, diagnostic)
    if run is None:
        _retained(root, calls)
    else:
        for call in run.calls:
            if call.position < len(calls):
                previous = calls[call.position]
                calls[call.position] = previous.model_copy(
                    update={"attempts": (*previous.attempts, *call.attempts)}
                )
    return calls
