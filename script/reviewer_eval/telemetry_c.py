# SPDX-License-Identifier: Apache-2.0
"""Offline process and transport observations for the retained C blocks."""

import argparse
from collections import Counter
from collections.abc import Sequence
import csv
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import io
import json
import math
from pathlib import Path
import re
import sys
import tempfile
import textwrap

from pydantic import TypeAdapter

from script.eval.model import AttemptRecord, RunRecord
from script.reviewer_eval.c_models import Identities, Inventory, InventoryRow
from script.reviewer_eval.c_resources import telemetry, validate_identity
from script.reviewer_eval.report import CallOutcome, inspect_evidence
from script.reviewer_eval.transcript import (
    CODE_MODE_DISABLED_NOTICE,
    _fallback,
    _reconnect,
    parse_json,
)
from script.reviewer_eval.verify_c_archive import extract, verify_launcher


@dataclass(frozen=True)
class Attempt:
    """Public, answer-free projection of one process observation."""

    block: str
    effort: str
    position: int
    number: int
    state: str
    terminal_success: bool
    answer_present: bool
    start: str
    end: str | None
    elapsed: float | None
    reconnect: int
    fallback: int
    unknown_errors: int
    status_403: int
    status_429: int
    status_503: int
    overloaded: int
    local_exception: bool
    usage: dict[str, int | None]


def notices(raw: bytes) -> tuple[int, int, int, int, int, int, int]:
    """Count only error-event messages, never response or reasoning text.

    Returns:
        Reconnects, fallbacks, unknown errors, 403, 429, 503, and overload counts.
    """
    counts = [0] * 7
    for line in raw.splitlines():
        try:
            event = parse_json(line)
        except ValueError:
            counts[2] += 1
            continue
        if not isinstance(event, dict):
            counts[2] += 1
            continue
        count_event(counts, event)
    return counts[0], counts[1], counts[2], counts[3], counts[4], counts[5], counts[6]


def error_payload(event: dict[str, object]) -> dict[str, object] | None:
    """Select structured error events while excluding model message bodies.

    Returns:
        The error object or None.
    """
    if event.get("type") == "error":
        return event
    nested = event.get("error")
    if event.get("jsonrpc") == "2.0" and isinstance(nested, dict):
        return nested
    item = event.get("item")
    if (
        event.get("type") == "item.completed"
        and isinstance(item, dict)
        and item.get("type") == "error"
    ):
        return item
    return None


def count_event(counts: list[int], event: dict[str, object]) -> None:
    """Classify a single decoded event without inspecting answer text."""
    error = error_payload(event)
    if error is None:
        return
    counts[6] += int(error.get("code") == -32001)
    nested_error = error.get("error")
    if isinstance(nested_error, dict):
        counts[6] += int(nested_error.get("code") == -32001)
    message = error.get("message")
    if _reconnect(event):
        counts[0] += 1
    elif event.get("type") == "item.completed" and _fallback(error):
        counts[1] += 1
    elif isinstance(message, str) and message == CODE_MODE_DISABLED_NOTICE:
        return
    else:
        counts[2] += 1
    if isinstance(message, str):
        add_status_counts(counts, message)


def add_status_counts(counts: list[int], message: str) -> None:
    """Count known structured diagnostics in an error message."""
    for index, pattern in enumerate(
        (
            r"unexpected status 403\b",
            r"unexpected status 429\b",
            r"unexpected status 503\b",
        ),
        start=3,
    ):
        counts[index] += len(re.findall(pattern, message))


def distribution(values: Sequence[float | int | None]) -> dict[str, float | int | None]:
    """Summarize finite values using linear interpolation at (n-1)*p.

    Returns:
        Known and missing counts, extrema, mean, and percentiles.
    """
    known = sorted(float(v) for v in values if v is not None and math.isfinite(v))
    result: dict[str, float | int | None] = {
        "known": len(known),
        "missing": len(values) - len(known),
        "min": min(known) if known else None,
        "max": max(known) if known else None,
        "mean": sum(known) / len(known) if known else None,
    }
    for p in (50, 90, 95, 99):
        if not known:
            result[f"p{p}"] = None
            continue
        index = (len(known) - 1) * p / 100
        lo, hi = math.floor(index), math.ceil(index)
        result[f"p{p}"] = known[lo] + (known[hi] - known[lo]) * (index - lo)
    return result


def timestamp(value: str) -> float:
    """Parse a timezone-aware UTC timestamp into seconds.

    Returns:
        Unix seconds.

    Raises:
        ValueError: The timestamp is invalid or not UTC.
    """
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ValueError("timestamp is not UTC")
    return parsed.timestamp()


def timeline(intervals: list[tuple[float, float]]) -> dict[str, float | int]:
    """Sweep half-open intervals, with end events before starts at ties.

    Returns:
        Peak, window, active union, mean occupancy and start span.

    Raises:
        ValueError: An interval is invalid.
    """
    if not intervals or any(
        not math.isfinite(a) or not math.isfinite(b) or b <= a for a, b in intervals
    ):
        raise ValueError("invalid process interval")
    events = sorted([(a, 1) for a, _ in intervals] + [(b, -1) for _, b in intervals])
    active = peak = 0
    area = union = 0.0
    previous = events[0][0]
    for when, change in events:
        delta = when - previous
        area += active * delta
        union += delta if active else 0
        active += change
        peak = max(peak, active)
        previous = when
    window = events[-1][0] - events[0][0]
    starts = [a for a, _ in intervals]
    return {
        "peak": peak,
        "window_seconds": window,
        "active_union_seconds": union,
        "mean_active_over_window": area / window,
        "start_span_seconds": max(starts) - min(starts),
    }


def summarize(rows: list[Attempt]) -> dict[str, object]:
    """Summarize one explicitly selected attempt group.

    Returns:
        Counts and distributions with explicit denominators.
    """
    result: dict[str, object] = {
        "attempts": len(rows),
        "states": dict(sorted(Counter(r.state for r in rows).items())),
        "terminal_success": sum(r.terminal_success for r in rows),
        "answer_present": sum(r.answer_present for r in rows),
        "terminal_failure": sum(not r.terminal_success for r in rows),
        "failed_with_unknown_error": sum(
            not r.terminal_success and r.unknown_errors > 0 for r in rows
        ),
        "profiles": profiles(rows),
    }
    result.update(notice_summary(rows))
    result["local_exceptions"] = sum(r.local_exception for r in rows)
    result["elapsed_seconds"] = distribution([r.elapsed for r in rows])
    result.update(recovery_latencies(rows))
    result["usage"] = usage_summary(rows)
    result["recovery_usage"] = usage_summary([
        r for r in rows if r.reconnect or r.fallback
    ])
    return result


def recovery_latencies(rows: list[Attempt]) -> dict[str, object]:
    """Describe latency for observed recovery profiles.

    Returns:
        Distributions for recovery and no-recovery attempts.
    """
    recovered = [r.elapsed for r in rows if r.reconnect or r.fallback]
    clean = [r.elapsed for r in rows if not r.reconnect and not r.fallback]
    return {
        "recovery_elapsed_seconds": distribution(recovered),
        "no_recovery_elapsed_seconds": distribution(clean),
    }


def profiles(rows: list[Attempt]) -> dict[str, int]:
    """Count mutually exclusive observed transport profiles.

    Returns:
        Attempt counts for each profile.
    """
    counts = Counter((bool(r.reconnect), bool(r.fallback)) for r in rows)
    return {
        "none": counts[False, False],
        "reconnect_only": counts[True, False],
        "fallback_only": counts[False, True],
        "both": counts[True, True],
    }


def notice_summary(rows: list[Attempt]) -> dict[str, object]:
    """Count notices and distinct attempts by diagnostic class.

    Returns:
        Counts keyed by diagnostic class.
    """
    result: dict[str, object] = {}
    for key in (
        "reconnect",
        "fallback",
        "unknown_errors",
        "status_403",
        "status_429",
        "status_503",
        "overloaded",
    ):
        result[key] = {
            "notices": sum(getattr(r, key) for r in rows),
            "attempts": sum(getattr(r, key) > 0 for r in rows),
        }
    return result


def valid_usage(value: int | None) -> int | None:
    """Retain nonnegative token counts, otherwise leave the category unknown.

    Returns:
        The count or None.
    """
    return value if value is not None and value >= 0 else None


def usage_summary(rows: list[Attempt]) -> dict[str, object]:
    """Summarize complete usage categories for a selected subset.

    Returns:
        Totals and distributions per category.
    """
    result: dict[str, object] = {}
    for key in (
        "input_tokens",
        "cached_input_tokens",
        "cache_write_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    ):
        values = [valid_usage(row.usage[key]) for row in rows]
        result[key] = {
            "total": sum(v for v in values if v is not None)
            if all(v is not None for v in values)
            else None,
            "distribution": distribution(values),
        }
    return result


def project_attempt(
    name: str, root: Path, call: CallOutcome, attempt: AttemptRecord
) -> Attempt:
    """Project one inspected attempt without retaining its response.

    Returns:
        Public attempt metrics.
    """
    digest = sha256(attempt.call_id.encode()).hexdigest()
    stream = (
        root
        / "attempts"
        / f"position-{attempt.position}"
        / digest
        / f"attempt-{attempt.attempt_number}.stdout"
    )
    counts = notices(stream.read_bytes()) if stream.exists() else (0, 0, 1, 0, 0, 0, 0)
    usage = telemetry(attempt)[1]
    categories = {
        key: getattr(usage, key) if usage else None
        for key in (
            "input_tokens",
            "cached_input_tokens",
            "cache_write_input_tokens",
            "output_tokens",
            "reasoning_output_tokens",
        )
    }
    return Attempt(
        name,
        call.effort,
        call.position,
        attempt.attempt_number,
        call.state,
        attempt.outcome_kind == "completed" and attempt.exit_status == 0,
        call.selected_attempt == attempt.attempt_number,
        attempt.started_at_utc,
        attempt.ended_at_utc,
        attempt.elapsed_seconds,
        *counts,
        attempt.error_type is not None,
        categories,
    )


def read_block(
    evidence: Path,
    name: str,
    inventory: Inventory,
    identities: Identities,
    seen: set[str],
    root: Path,
) -> tuple[list[Attempt], dict[str, object]]:
    """Verify and inspect one block, then project its attempts.

    Returns:
        Answer-free attempts and block timing/binding observations.

    Raises:
        ValueError: The archive or observation is inconsistent.
    """
    rows = TypeAdapter(list[InventoryRow]).validate_json(
        (evidence / inventory.blocks[name]).read_bytes()
    )
    archive = inventory.archives[name]
    if (
        archive.file != name + ".tar.gz"
        or inventory.blocks[name] != f"inventory/{name}.json"
    ):
        raise ValueError("unsafe archive inventory name")
    extract(evidence / archive.file, root, rows, archive.sha256)
    inspection = inspect_evidence(root)
    if inspection.plan is None or inspection.report.evidence_state == "invalid":
        raise ValueError(f"invalid block: {name}")
    validate_identity(
        inspection, identities.blocks[name], identities.ordered_prompt_sha256, seen
    )
    run = RunRecord.model_validate_json((root / "run.json").read_bytes())
    projected = [
        project_attempt(name, root, call, attempt)
        for call in inspection.report.calls
        for attempt in call.attempts
    ]
    intervals = [
        (timestamp(r.start), timestamp(r.end)) for r in projected if r.end is not None
    ]
    if len(intervals) != len(projected):
        raise ValueError("missing process end timestamp")
    timing = timeline(intervals)
    timing["answer_present_per_minute"] = (
        60 * sum(r.answer_present for r in projected) / timing["window_seconds"]
    )
    timing["complete_per_minute"] = (
        60 * sum(r.state == "complete" for r in projected) / timing["window_seconds"]
    )
    timing["terminal_success_per_minute"] = (
        60 * sum(r.terminal_success for r in projected) / timing["window_seconds"]
    )
    return projected, {
        "timeline": timing,
        "cli_version": run.cli_version,
        "runner_version": run.runner_version,
        "configured_concurrency": inspection.plan.configuration.concurrency,
        "planned_calls": len(inspection.plan.calls),
        "counts": inspection.report.counts.model_dump()
        if inspection.report.counts
        else None,
    }


def recovery_row(name: str, selected: list[Attempt]) -> str:
    """Render one recovery and latency table row.

    Returns:
        Markdown table row.
    """
    stats = distribution([r.elapsed for r in selected])
    median, p95 = stats["p50"], stats["p95"]
    median_text = f"{median:.2f}" if median is not None else "unknown"
    p95_text = f"{p95:.2f}" if p95 is not None else "unknown"
    recovered = sum(bool(r.reconnect or r.fallback) for r in selected)
    fallback = (
        100 * sum(bool(r.fallback) for r in selected) / len(selected) if selected else 0
    )
    return (
        f"| {name} | {recovered}/{len(selected)} | {fallback:.2f}% | "
        f"{median_text} | {p95_text} | {stats['known']}/{stats['missing']} |"
    )


def recovery_groups(rows: list[Attempt]) -> list[tuple[str, list[Attempt]]]:
    """Select blocks, efforts and overall recovery subsets.

    Returns:
        Named groups of attempts.
    """
    groups = [
        (name, [r for r in rows if r.block == name])
        for name in sorted({r.block for r in rows})
    ]
    groups += [
        (effort, [r for r in rows if r.effort == effort])
        for effort in ("none", "low", "medium", "high")
    ]
    groups += [
        ("Recovery overall", [r for r in rows if r.reconnect or r.fallback]),
        (
            "No recovery overall",
            [r for r in rows if not r.reconnect and not r.fallback],
        ),
    ]
    return groups


def recovery_table(rows: list[Attempt]) -> list[str]:
    """Summarize observed recovery and latency by block and effort.

    Returns:
        Markdown table and method text.
    """
    lines = [
        "",
        "| Group | Recovery/attempts | Fallback % | Elapsed p50 s | "
        "Elapsed p95 s | Known/missing |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    groups = recovery_groups(rows)
    for name, selected in groups:
        lines.append(recovery_row(name, selected))
    return lines


def markdown(
    rows: list[Attempt], blocks: dict[str, object], overall: dict[str, float | int]
) -> bytes:
    """Render a concise public interpretation of the measured process records.

    Returns:
        UTF-8 Markdown.
    """
    summary = summarize(rows)
    versions = sorted({
        str(item["cli_version"]) for item in blocks.values() if isinstance(item, dict)
    })
    concurrencies = sorted({
        str(item["configured_concurrency"])
        for item in blocks.values()
        if isinstance(item, dict)
    })
    profiles = summary["profiles"]
    assert isinstance(profiles, dict)
    lines = [
        "# C process and transport telemetry",
        "",
        f"{sum(r.terminal_success for r in rows):,} of {len(rows):,} CLI processes "
        f"finished successfully; configured concurrency: {', '.join(concurrencies)}; "
        f"{sum(r.state == 'complete' for r in rows):,} responses were schema-complete "
        f"and {sum(r.state == 'invalid' for r in rows)} were invalid. "
        "The previously documented 22 "
        "recorded boundary-affected calls remain separate from these "
        "structural counts.",
        "",
        f"{profiles['reconnect_only'] + profiles['both']:,}/{len(rows):,} "
        f"({100 * (profiles['reconnect_only'] + profiles['both']) / len(rows):.2f}%) "
        "attempts emitted reconnect "
        f"notices and {profiles['fallback_only'] + profiles['both']:,}/{len(rows):,} "
        f"({100 * (profiles['fallback_only'] + profiles['both']) / len(rows):.2f}%) "
        f"emitted HTTPS fallback "
        f"notices; {profiles['both']:,} had both and {profiles['none']:,} had neither. "
        f"These include {sum(r.reconnect for r in rows):,} reconnect and "
        f"{sum(r.fallback for r in rows):,} fallback notices, and "
        f"{sum(r.status_403 for r in rows):,} status-403 occurrences across "
        f"{sum(r.status_403 > 0 for r in rows):,} attempts. "
        f"Structured 429, 503, and -32001 occurrences are "
        f"{sum(r.status_429 for r in rows)}, {sum(r.status_503 for r in rows)}, and "
        f"{sum(r.overloaded for r in rows)}; unknown error events are "
        f"{sum(r.unknown_errors for r in rows)}. "
        "The notices describe recovery within one CLI process, not harness retries. "
        f"Recorded CLI versions: {', '.join(versions)}. The Codex 0.166 source "
        "behavior examined in the earlier investigation hides the first WebSocket "
        "retry; emitted notices do not count physical attempts.",
        "",
        "The recorded blocks each have 186 calls and one attempt per call. "
        "This establishes completion for this workload with recovery, not "
        "an optimal concurrency, "
        "a subscription limit, or a speedup over serial execution. The 403 WebSocket "
        "diagnostics and fallback do not establish rate limiting. Server "
        "queue time, inference "
        "time, and retry delays have no timestamps here. Process activity "
        "is not inference.",
        "",
        "| Block | Window seconds | Answers/min | Schema-complete/min | "
        "Peak active | Mean active | Start span seconds |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, item in blocks.items():
        assert isinstance(item, dict)
        timing = item["timeline"]
        assert isinstance(timing, dict)
        lines.append(
            f"| {name} | {timing['window_seconds']:.2f} | "
            f"{timing['answer_present_per_minute']:.2f} | "
            f"{timing['complete_per_minute']:.2f} | {timing['peak']} | "
            f"{timing['mean_active_over_window']:.2f} | "
            f"{timing['start_span_seconds']:.2f} |"
        )
    lines.extend(recovery_table(rows))
    lines.extend([
        "",
        "Windows span earliest process start through latest end; rates use each "
        "block's window and exclude launch and cleanup outside it. Mean active is the "
        "integral of simultaneous process intervals divided by that window. Intervals "
        "are half-open; ties end before starts. Across all blocks, the union of active "
        f"intervals is {overall['active_union_seconds']:.2f} seconds, while the actual "
        f"first-start to last-end span is {overall['window_seconds']:.2f} seconds, "
        "including idle gaps.",
        "",
        "The JSON retains per-block, effort and all-attempt counts, token categories, "
        "and elapsed distributions. Percentiles interpolate linearly at (n-1)p; "
        "each distribution records known and missing counts. Elapsed seconds are "
        "supervisor observations including startup and recovery. Recovery and "
        "no-recovery groups differ in effort, timing, task and cache mix; their "
        "distributions do not establish a causal latency effect. Cached input is "
        "included in input, and reasoning is included in output. No cost is inferred.",
        "",
        "HTTP status counts cover `unexpected status` diagnostics in error "
        "events, not arbitrary answer text. Numeric -32001 counts cover direct and "
        "nested structured error code fields only. Counts describe occurrences and "
        "distinct attempts; the same 403 can appear in reconnect and fallback notices. "
        "Unknown error shapes are counted separately. Original archives, inventories "
        "and launcher metadata are verified before analysis; inspection checks "
        "internal consistency and byte provenance, not authenticated lineage or "
        "safe-read enforcement. The pilot ran first; the remaining blocks followed "
        "the recorded order. The next measurement would vary concurrency on matched "
        "workloads and capture server-side timing if available.",
        "",
    ])
    return "\n".join(
        line if line.startswith("|") else textwrap.fill(line, width=79)
        for line in lines
    ).encode()


def generate(evidence: Path) -> dict[str, bytes]:
    """Derive deterministic artifacts from verified saved evidence.

    Returns:
        Output filenames and bytes.

    Raises:
        ValueError: The evidence is inconsistent.
    """
    inventory = Inventory.model_validate_json(
        (evidence / "inventory.json").read_bytes()
    )
    identities = Identities.model_validate_json(
        (evidence / "block-identities.json").read_bytes()
    )
    verify_launcher(evidence, inventory.launcher_evidence)
    blocks: dict[str, object] = {}
    all_rows: list[Attempt] = []
    seen: set[str] = set()
    with tempfile.TemporaryDirectory() as tmp:
        for name in sorted(inventory.blocks):
            if Path(name).name != name or name in {".", ".."}:
                raise ValueError("unsafe block name")
            rows, details = read_block(
                evidence, name, inventory, identities, seen, Path(tmp) / name
            )
            blocks[name] = {**details, "summary": summarize(rows)}
            all_rows.extend(rows)
    inputs = {
        name: sha256((evidence / name).read_bytes()).hexdigest()
        for name in [
            "inventory.json",
            "block-identities.json",
            *sorted(inventory.blocks.values()),
        ]
    }
    inputs.update({item.file: item.sha256 for item in inventory.archives.values()})
    summary = {
        "method": "C retained telemetry; linear percentile interpolation at (n-1)*p",
        "base_revision": "d28438df92580c50703902341ec639a612bf0aaf",
        "code_sha256": {
            str(path): sha256(path.read_bytes()).hexdigest()
            for path in (
                Path("script/reviewer_eval/telemetry_c.py"),
                Path("script/reviewer_eval/transcript.py"),
                Path("script/reviewer_eval/c_resources.py"),
                Path("script/reviewer_eval/verify_c_archive.py"),
                Path("script/reviewer_eval/report.py"),
            )
        },
        "inputs_sha256": inputs,
        "blocks": blocks,
        "efforts": {
            effort: summarize([r for r in all_rows if r.effort == effort])
            for effort in ("none", "low", "medium", "high")
        },
        "all": summarize(all_rows),
        "timeline_all": timeline([
            (timestamp(r.start), timestamp(r.end))
            for r in all_rows
            if r.end is not None
        ]),
    }
    data = (
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow([
        "block",
        "effort",
        "position",
        "number",
        "state",
        "terminal_success",
        "answer_present",
        "start",
        "end",
        "elapsed",
        "reconnect",
        "fallback",
        "unknown_errors",
        "status_403",
        "status_429",
        "status_503",
        "overloaded",
        "local_exception",
        "input_tokens",
        "cached_input_tokens",
        "cache_write_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    ])
    for row in all_rows:
        writer.writerow([
            row.block,
            row.effort,
            row.position,
            row.number,
            row.state,
            row.terminal_success,
            row.answer_present,
            row.start,
            row.end,
            row.elapsed,
            row.reconnect,
            row.fallback,
            row.unknown_errors,
            row.status_403,
            row.status_429,
            row.status_503,
            row.overloaded,
            row.local_exception,
            *row.usage.values(),
        ])
    detail = stream.getvalue().encode()
    return {
        "telemetry.json": data,
        "telemetry-attempts.csv": detail,
        "telemetry.md": markdown(all_rows, blocks, summary["timeline_all"]),
    }


def check_artifact(name: str, generated: bytes, retained: bytes) -> tuple[str, ...]:
    """Compare retained observations while reporting historical code drift.

    Returns:
        Paths whose retained code digests differ from the current analysis.

    Raises:
        ValueError: The artifact or its provenance structure differs.
    """
    if name != "telemetry.json":
        if retained != generated:
            raise ValueError(f"artifact differs: {name}")
        return ()
    old = json.loads(retained)
    current = json.loads(generated)
    if not isinstance(old, dict) or not isinstance(current, dict):
        raise ValueError("invalid telemetry summary")
    old_code = old.get("code_sha256")
    current_code = current.get("code_sha256")
    if not isinstance(old_code, dict) or not isinstance(current_code, dict):
        raise ValueError("invalid telemetry code provenance")
    if old_code.keys() != current_code.keys():
        raise ValueError("telemetry code provenance paths differ")
    if any(
        not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None
        for value in (*old_code.values(), *current_code.values())
    ):
        raise ValueError("invalid telemetry code provenance digest")
    canonical = (
        json.dumps(current, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    if canonical != generated:
        raise ValueError(f"artifact differs: {name}")
    changed = tuple(
        sorted(path for path in old_code if old_code[path] != current_code[path])
    )
    current["code_sha256"] = old_code
    normalized = (
        json.dumps(current, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    if normalized != retained:
        raise ValueError(f"artifact differs: {name}")
    return changed


def main() -> None:
    """Generate into a fresh directory or compare with retained artifacts."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    artifacts = generate(args.evidence)
    if not args.check:
        args.output.mkdir(parents=True, exist_ok=False)
    for name, data in artifacts.items():
        target = args.output / name
        if args.check:
            changed = check_artifact(name, data, target.read_bytes())
            if changed:
                sys.stderr.write(
                    "Retained code provenance differs from current analysis: "
                    + ", ".join(changed)
                    + "\n"
                )
        else:
            target.write_bytes(data)


if __name__ == "__main__":
    main()
