# SPDX-License-Identifier: Apache-2.0
"""Derive resource totals from retained attempts without inventing usage."""

from datetime import datetime
from hashlib import sha256
from typing import Literal

from pydantic import BaseModel, ValidationError

from script.eval.model import AttemptRecord
from script.reviewer_eval.c_models import BlockIdentity
from script.reviewer_eval.report import Inspection, Report


class Usage(BaseModel):
    """Provider categories may be absent."""

    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    cache_write_input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_output_tokens: int | None = None


class Event(BaseModel):
    """Relevant fields from one retained telemetry event."""

    type: str
    thread_id: str | None = None
    usage: Usage | None = None


def telemetry(attempt: AttemptRecord) -> tuple[str | None, Usage | None]:
    """Extract the thread and usage, leaving absent or malformed values unknown.

    Returns:
        Thread ID and usage when each is available.
    """
    try:
        events = [
            Event.model_validate_json(line)
            for line in (attempt.usage_telemetry or b"").splitlines()
        ]
    except ValidationError:
        return None, None
    threads = [e.thread_id for e in events if e.type == "thread.started"]
    usages = [e.usage for e in events if e.type == "turn.completed"]
    return (
        threads[0] if len(threads) == 1 else None,
        usages[0] if len(usages) == 1 else None,
    )


def validate_identity(
    inspection: Inspection, identity: BlockIdentity, order: list[str], seen: set[str]
) -> None:
    """Bind a block and every observed thread to its factual identity.

    Raises:
        ValueError: Identity, ordering, or thread uniqueness differs.
    """
    plan = inspection.plan
    if (
        plan is None
        or plan.run_id != identity.run_id
        or plan.configuration.concurrency != identity.concurrency
    ):
        raise ValueError("run identity mismatch")
    if [c.position for c in plan.calls] != list(range(186)) or [
        c.prompt_sha256 for c in plan.calls
    ] != order:
        raise ValueError("planned packet order mismatch")
    if any(
        c.model != identity.model or c.effort != identity.effort for c in plan.calls
    ):
        raise ValueError("model or effort identity mismatch")
    threads = [telemetry(a)[0] for c in inspection.report.calls for a in c.attempts]
    known = [t for t in threads if t is not None]
    if len(known) != len(set(known)) or set(known) & seen:
        raise ValueError("duplicate thread identity")
    if (
        len(known) == 186
        and sha256(("\n".join(sorted(known)) + "\n").encode()).hexdigest()
        != identity.thread_ids_sha256
    ):
        raise ValueError("thread identity mismatch")
    seen.update(known)


def complete_sum(values: list[int | None]) -> int | None:
    """Sum a nonempty complete category, preserving missing values.

    Returns:
        Total or None.
    """
    if not values or any(v is None for v in values):
        return None
    return sum(v for v in values if v is not None)


def totals(usages: list[Usage | None], baseline: int) -> dict[str, int | None]:
    """Sum complete categories and retain signed baseline adjustments.

    Returns:
        Each total, or None when any constituent is unknown.
    """
    keys = (
        "input_tokens",
        "cached_input_tokens",
        "cache_write_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    )
    result: dict[str, int | None] = {}
    for key in keys:
        values = [getattr(u, key) if u is not None else None for u in usages]
        result[key] = complete_sum(values)
    raw = result["input_tokens"]
    output = result["output_tokens"]
    adjusted = raw - baseline * len(usages) if raw is not None else None
    result["candidate_adjusted_input"] = adjusted
    result["candidate_adjusted_complete"] = (
        adjusted + output if adjusted is not None and output is not None else None
    )
    return result


def timings(attempts: list[AttemptRecord]) -> tuple[float | None, float | None]:
    """Calculate observed attempt timing.

    Returns:
        Window and summed duration if available.
    """
    try:
        starts = [
            datetime.fromisoformat(a.started_at_utc.replace("Z", "+00:00"))
            for a in attempts
        ]
        ends = [
            datetime.fromisoformat(a.ended_at_utc.replace("Z", "+00:00"))
            for a in attempts
            if a.ended_at_utc
        ]
        window = (
            round((max(ends) - min(starts)).total_seconds(), 2)
            if starts and len(ends) == len(attempts)
            else None
        )
    except ValueError:
        window = None
    elapsed = (
        round(
            sum(a.elapsed_seconds for a in attempts if a.elapsed_seconds is not None), 2
        )
        if attempts and all(a.elapsed_seconds is not None for a in attempts)
        else None
    )
    return window, elapsed


def resources(
    report: Report, effort: Literal["none", "low", "medium", "high"]
) -> tuple[dict[str, int | None], float | None, float | None]:
    """Compute all-attempt usage and timing with unknown propagation.

    Returns:
        Resource totals, attempt window, and aggregate duration.
    """
    attempts = [a for c in report.calls for a in c.attempts]
    usage = [telemetry(a)[1] for a in attempts]
    # A missing attempt makes complete block totals unknown.
    if any(not c.attempts for c in report.calls):
        usage.append(None)
    total = totals(usage, 3568 if effort == "low" else 3570)
    window, elapsed = timings(attempts)
    if any(not c.attempts for c in report.calls):
        elapsed = None
    return total, window, elapsed
