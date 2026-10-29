# SPDX-License-Identifier: Apache-2.0
"""Pure serialization choices for coordinator records."""

from hashlib import sha256
import json

from script.eval.model import CallRecord, RunRecord, SettingValue
from script.eval.model import CallState as PersistedCallState
from script.eval.runner.ports import BoundRun

from .call_states import CallState, EvidencePending, Finished
from .quota_states import QuotaHistory


def settings_digest(settings: tuple[tuple[str, SettingValue], ...], /) -> str:
    """Hash ordered binding settings using compact UTF-8 JSON.

    The input's order and scalar types are retained. JSON uses UTF-8 directly,
    no insignificant whitespace, and rejects non-finite floats. This digest
    identifies precisely the supplied binding settings, not a call identity.

    Returns:
        The lowercase SHA-256 hexadecimal digest of the encoded settings.

    Non-finite floating-point values raise ValueError.
    """
    encoded = json.dumps(
        settings, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def call_record(bound: BoundRun, state: CallState, digest: str, /) -> CallRecord:
    """Project one call's immutable identity and only its durable attempts.

    Evidence-pending is a coarse execution failure in the persisted record;
    live progress separately retains that unfinished obligation.

    Returns:
        The call record for this exact scheduled position.
    """
    history = state.history
    call = history.call
    plan = bound.plan
    planned = call.planned_call
    sources = tuple(plan.snapshots[index] for index in planned.context_indices)
    if isinstance(state, Finished) and state.outcome == "success":
        status: PersistedCallState = "complete"
    elif isinstance(state, EvidencePending):
        status = "failed"
    elif not history.attempts:
        status = "not_started"
    else:
        status = "failed"
    return CallRecord(
        run_id=call.run_id,
        call_id=call.call_id,
        position=planned.position,
        state=status,
        source_paths=tuple(source.repository_path for source in sources),
        source_sha256=tuple(source.content_sha256 for source in sources),
        boundary_bytes_hex=tuple(boundary.hex() for boundary in plan.boundary_bytes),
        prompt_sha256=planned.prompt_sha256,
        model=planned.model,
        effort=planned.effort,
        effective_settings_sha256=digest,
        attempts=history.attempts,
    )


def run_record(
    bound: BoundRun,
    states: tuple[CallState, ...],
    quota: QuotaHistory,
    incomplete: bool,
    digest: str,
    /,
) -> RunRecord:
    """Build final accounting from the frozen plan and settled histories.

    Returns:
        A record ready for the evidence store's retained final write.
    """
    plan, binding = bound.plan, bound.binding
    return RunRecord(
        run_id=plan.run_id,
        repository_root=str(plan.repository_root),
        head_commit=plan.head_commit,
        state="incomplete" if incomplete else "complete",
        runner_version=binding.runner_version,
        codex_path=str(binding.executable_path),
        cli_version=binding.cli_version,
        effective_settings=binding.effective_settings,
        calls=tuple(call_record(bound, state, digest) for state in states),
        waits=tuple(wait for state in states for wait in state.history.waits)
        + quota.waits,
    )
