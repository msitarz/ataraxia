# SPDX-License-Identifier: Apache-2.0
"""Representative disposable parent caller for the public stop-hook boundary.

This fixture exercises a minimal call-site pattern, not the Evaluation runner,
its signal policy, scheduling, persistence, or scoring.
"""

import argparse
import asyncio
from contextlib import suppress
from dataclasses import dataclass, field
import json
from pathlib import Path
import signal
import sys
from time import monotonic, sleep
from typing import Literal, cast, override

type Trigger = Literal["SIGINT", "SIGTERM", "task-cancel", "record-failure"]
type UnsafeCleanup = Literal["signal", "wait"] | None

REPOSITORY_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(REPOSITORY_ROOT))

from script.process_supervisor import (  # ruff: ignore[module-import-not-at-top-of-file]
    AttemptCancelled,
    AttemptRequest,
    AttemptResult,
    CleanupEvidence,
    CleanupOutcome,
    Completed,
    NativeProcessEffects,
    ProcessHandle,
    SignalAttempt,
    call_supervisor,
    failure_evidence,
    run_attempt,
    stop_dispatch_diagnostic,
)

CHILD_FIXTURE = Path(__file__).with_name("process_supervisor_child.py")


@dataclass(frozen=True)
class CallerOptions:
    scenario: Literal["stop", "retry"]
    trigger: Trigger
    unsafe_cleanup: UnsafeCleanup
    fail_recording: bool
    workdir: Path
    ready_file: Path


@dataclass
class RepresentativeCaller:
    """Small call-site example with a dispatch latch and retained accounting."""

    pending: list[str]
    fail_recording: bool = False
    stopped: bool = False
    events: list[str] = field(default_factory=list)
    attempts: list[str] = field(default_factory=list)
    active_reason: str | None = None
    active_signals: list[dict[str, str | None]] = field(default_factory=list)
    active_wait: str | None = None
    not_started: list[str] = field(default_factory=list)
    stop_diagnostic: str | None = None

    def stop(self, reason: AttemptResult | BaseException, /) -> None:
        """Latch dispatch before recording active outcome evidence."""
        self.latch_stop()
        self.events.append("record_attempt")
        if self.fail_recording:
            raise RuntimeError("representative recorder failed")
        self.active_reason = type(reason).__name__
        evidence = (
            failure_evidence(reason) if isinstance(reason, BaseException) else None
        )
        observation = (
            reason.observation if not isinstance(reason, BaseException) else None
        )
        if evidence is not None:
            observation = evidence.observation
        if observation is not None:
            self.active_signals = [
                {
                    "signal": item.signal,
                    "outcome": item.outcome,
                    "diagnostic": item.diagnostic,
                }
                for item in observation.cleanup.signals
            ]
            self.active_wait = observation.cleanup.direct_wait
        self.events.append("recorded")

    def latch_stop(self) -> None:
        """Latch once, before cancellation or fallible status recording."""
        if not self.stopped:
            self.stopped = True
            self.events.append("latched")

    def dispatch(self, label: str) -> bool:
        """Claim a call only when the stop latch permits dispatch."""
        if self.stopped:
            self.events.append(f"dispatch-refused:{label}")
            self.not_started.append(label)
            return False
        self.attempts.append(label)
        return True


class UnsafeReportingEffects(NativeProcessEffects):
    """Perform native cleanup but report the selected unsafe boundary result."""

    def __init__(self, unsafe_field: Literal["signal", "wait"]) -> None:
        self.unsafe_field = unsafe_field

    @override
    async def cleanup(
        self, handle: ProcessHandle, timeout_seconds: float, grace_seconds: float, /
    ) -> CleanupOutcome:
        outcome = await super().cleanup(handle, timeout_seconds, grace_seconds)
        actual = outcome.evidence
        if self.unsafe_field == "signal":
            evidence = CleanupEvidence(
                actual.process,
                (SignalAttempt("SIGKILL", "failed", "injected signal diagnostic"),),
                actual.direct_wait,
                actual.wait_diagnostic,
            )
        else:
            evidence = CleanupEvidence(
                actual.process,
                actual.signals,
                "unknown",
                "injected wait diagnostic",
            )
        return CleanupOutcome(evidence, outcome.exit_status)


def request(
    workdir: Path,
    ready_file: Path,
    mode: str,
    *arguments: str,
    timeout_seconds: float = 5.0,
) -> AttemptRequest:
    """Build one bounded request for the real CLI fixture."""
    child_arguments = (*arguments, "--ready-file", str(ready_file))
    return AttemptRequest(
        (sys.executable, str(CHILD_FIXTURE), mode, *child_arguments),
        workdir,
        timeout_seconds,
        2.0,
        0,
        "devnull",
    )


def wait_for_file(path: Path, timeout_seconds: float) -> None:
    """Wait for a fixture handshake with a bounded monotonic deadline."""
    deadline = monotonic() + timeout_seconds
    while not path.exists():
        if monotonic() >= deadline:
            raise TimeoutError(f"fixture handshake did not arrive: {path}")
        sleep(0.005)


async def run_stopped_call(args: CallerOptions) -> dict[str, object]:
    caller = RepresentativeCaller(["later-call"], args.fail_recording)
    effects = selected_effects(args)
    control = SignalControl(args.trigger, caller)
    control.install()
    active_task = start_active_attempt(args, caller, effects, control)
    try:
        await deliver_trigger(args, caller, active_task, control.stop_event)
        await record_active_outcome(caller, active_task)
        await dispatch_pending(caller, args)
        return report(caller, args)
    finally:
        await control.finish(active_task)


def selected_effects(args: CallerOptions) -> NativeProcessEffects:
    if args.unsafe_cleanup is None:
        return NativeProcessEffects()
    return UnsafeReportingEffects(args.unsafe_cleanup)


class SignalControl:
    """Map disposable caller signals to cancellation of its active attempt."""

    def __init__(self, trigger: Trigger, caller: RepresentativeCaller) -> None:
        self.trigger = trigger
        self.caller = caller
        self.stop_event = asyncio.Event()
        self.loop = asyncio.get_running_loop()
        self.handled_signal: signal.Signals | None = None

    def receive(self, active_task: asyncio.Task[AttemptResult]) -> None:
        self.caller.latch_stop()
        self.caller.events.append("cancel-requested")
        self.stop_event.set()
        if not active_task.done():
            active_task.cancel()

    def install(self) -> None:
        match self.trigger:
            case "SIGINT":
                self.handled_signal = signal.SIGINT
            case "SIGTERM":
                self.handled_signal = signal.SIGTERM
            case _:
                self.handled_signal = None

    def install_handler(self, active_task: asyncio.Task[AttemptResult]) -> None:
        if self.handled_signal is not None:
            self.loop.add_signal_handler(self.handled_signal, self.receive, active_task)

    async def finish(self, active_task: asyncio.Task[AttemptResult]) -> None:
        if self.handled_signal is not None:
            self.loop.remove_signal_handler(self.handled_signal)
        if not active_task.done():
            active_task.cancel()
            with suppress(BaseException):
                await active_task


def start_active_attempt(
    args: CallerOptions,
    caller: RepresentativeCaller,
    effects: NativeProcessEffects,
    control: SignalControl,
) -> asyncio.Task[AttemptResult]:
    attempt = request(
        Path(args.workdir),
        Path(args.ready_file),
        "sleep",
        "--stdout",
        "737461727465640a",
        timeout_seconds=0.6 if args.unsafe_cleanup else 5.0,
    )

    async def invoke(request_value: AttemptRequest, /) -> AttemptResult:
        return await run_attempt(request_value, effects)

    if not caller.dispatch("active-call"):
        raise RuntimeError("representative caller refused its first planned call")
    active_task = asyncio.create_task(call_supervisor(attempt, invoke, caller.stop))
    control.install_handler(active_task)
    return active_task


async def deliver_trigger(
    args: CallerOptions,
    caller: RepresentativeCaller,
    active_task: asyncio.Task[AttemptResult],
    stop_event: asyncio.Event,
) -> None:
    if args.unsafe_cleanup is not None:
        return
    if args.trigger in {"task-cancel", "record-failure"}:
        await asyncio.to_thread(wait_for_file, Path(args.ready_file), 3.0)
        caller.latch_stop()
        caller.events.append("cancel-requested")
        active_task.cancel()
    elif args.trigger in {"SIGINT", "SIGTERM"}:
        await asyncio.to_thread(wait_for_file, Path(args.ready_file), 3.0)
        sys.stdout.write("READY\n")
        sys.stdout.flush()
        await stop_event.wait()


async def record_active_outcome(
    caller: RepresentativeCaller, active_task: asyncio.Task[AttemptResult]
) -> None:
    try:
        result = await active_task
    except AttemptCancelled as error:
        caller.active_reason = type(error).__name__
        caller.active_signals = [
            {
                "signal": item.signal,
                "outcome": item.outcome,
                "diagnostic": item.diagnostic,
            }
            for item in error.observation.cleanup.signals
        ]
        caller.active_wait = error.observation.cleanup.direct_wait
        caller.stop_diagnostic = stop_dispatch_diagnostic(error)
    except BaseException as error:
        evidence = failure_evidence(error)
        if evidence is None:
            raise
        caller.active_reason = type(error).__name__
        caller.active_signals = [
            {
                "signal": item.signal,
                "outcome": item.outcome,
                "diagnostic": item.diagnostic,
            }
            for item in evidence.observation.cleanup.signals
        ]
        caller.active_wait = evidence.observation.cleanup.direct_wait
        caller.stop_diagnostic = stop_dispatch_diagnostic(error)
    else:
        if not result.observation.cleanup.dispatch_permitted:
            caller.stopped = True


async def dispatch_pending(caller: RepresentativeCaller, args: CallerOptions) -> None:
    """Attempt pending work through the caller's same stop guard."""
    while caller.pending:
        label = caller.pending.pop(0)
        if not caller.dispatch(label):
            continue
        marker = args.workdir / f"{label}-dispatched"
        attempt = request(
            args.workdir,
            args.ready_file,
            "emit",
            "--dispatch-marker",
            str(marker),
        )

        async def invoke(request_value: AttemptRequest, /) -> AttemptResult:
            return await run_attempt(request_value)

        await call_supervisor(attempt, invoke, caller.stop)


def report(caller: RepresentativeCaller, args: CallerOptions) -> dict[str, object]:
    """Return stable observations from the representative call site."""
    return {
        "stopped": caller.stopped,
        "events": caller.events,
        "attempts": caller.attempts,
        "active_reason": caller.active_reason,
        "active_signals": caller.active_signals,
        "active_wait": caller.active_wait,
        "not_started": caller.not_started,
        "stop_diagnostic": caller.stop_diagnostic,
        "followup_marker": (args.workdir / "later-call-dispatched").exists(),
    }


async def run_retry(args: CallerOptions) -> dict[str, object]:
    caller = RepresentativeCaller([])
    results: list[AttemptResult] = []
    first_direct_pid: int | None = None
    for label, status in (("first", 7), ("retry", 0)):
        if not caller.dispatch(label):
            continue
        attempt = request(
            args.workdir,
            args.ready_file,
            "emit",
            "--stdout",
            "72657472790a",
            "--status",
            str(status),
        )

        async def invoke(request_value: AttemptRequest, /) -> AttemptResult:
            return await run_attempt(request_value)

        result = await call_supervisor(attempt, invoke, caller.stop)
        results.append(result)
        if label == "first":
            direct_pid = int(args.ready_file.read_text(encoding="utf-8"))
            first_direct_pid = direct_pid
            caller.events.append(
                f"first-reaped:{direct_pid}:{result.exit_status}:"
                f"{result.observation.cleanup.direct_wait}"
            )
            if (
                isinstance(result, Completed)
                and result.exit_status == 7
                and result.observation.cleanup.dispatch_permitted
            ):
                caller.events.append("retry-dispatch")
            else:
                caller.latch_stop()
    return {
        "stopped": caller.stopped,
        "attempts": caller.attempts,
        "events": caller.events,
        "statuses": [result.exit_status for result in results],
        "cleanup": [
            {
                "signals": [
                    {
                        "signal": item.signal,
                        "outcome": item.outcome,
                        "diagnostic": item.diagnostic,
                    }
                    for item in result.observation.cleanup.signals
                ],
                "direct_wait": result.observation.cleanup.direct_wait,
            }
            for result in results
        ],
        "first_direct_pid": first_direct_pid,
    }


def parse_args() -> CallerOptions:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", choices=("stop", "retry"))
    parser.add_argument(
        "--trigger",
        choices=("SIGINT", "SIGTERM", "task-cancel", "record-failure"),
        default="task-cancel",
    )
    parser.add_argument("--unsafe-cleanup", choices=("signal", "wait"))
    parser.add_argument("--fail-recording", action="store_true")
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--ready-file", required=True)
    parsed = parser.parse_args()
    return CallerOptions(
        cast(Literal["stop", "retry"], parsed.scenario),
        cast(Trigger, parsed.trigger),
        cast(UnsafeCleanup, parsed.unsafe_cleanup),
        parsed.fail_recording,
        Path(parsed.workdir),
        Path(parsed.ready_file),
    )


async def main() -> int:
    args = parse_args()
    result = await (
        run_retry(args) if args.scenario == "retry" else run_stopped_call(args)
    )
    sys.stdout.write(json.dumps(result, sort_keys=True) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
