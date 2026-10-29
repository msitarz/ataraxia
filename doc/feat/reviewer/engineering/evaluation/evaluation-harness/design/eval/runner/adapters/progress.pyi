# SPDX-License-Identifier: Apache-2.0
"""Progress admission and standalone writer lifecycle.

The runtime modules implement this boundary; AC-9 completion remains open.
"""

from typing import Literal, Protocol

from ..ports import ProgressSnapshot, Runtime  # ruff: ignore[relative-imports]

type Admission = Literal["accepted", "dropped", "unavailable"]

class ProgressAdmission(Protocol):
    """Offer one bounded message without waiting for output or a worker.

    Messages are UTF-8 and bounded to 16 KiB. ``accepted`` acknowledges
    admission only, not delivery. A pending message may be replaced or discarded
    at shutdown. Routine messages cannot replace a pending important message.
    ``dropped`` means this message was not admitted; ``unavailable`` disables
    subsequent presentation.
    """

    def __call__(self, text: str, /, *, important: bool = False) -> Admission: ...

class ProgressWriter(ProgressAdmission, Protocol):
    """Own one daemon writer and its duplicate stderr descriptor.

    The worker retains at most one claimed message and one pending message.
    It owns a non-inheritable duplicated descriptor until it exits, including
    after close. A partial TTY write may leave a visible fragment.
    A partial or failed write disables presentation without retrying a suffix.
    """

    def close(self) -> None:
        """Stop admission and discard pending output without waiting or joining.

        One already claimed write may remain blocked after close; the daemon
        worker closes its own descriptor after that attempt returns. Close does
        not close the caller's descriptor or change its file-status flags.
        """
        ...

def open_progress_writer(stderr_fd: int, /) -> ProgressWriter | None:
    """Duplicate stderr and start one daemon writer for an execution.

    Return None on ordinary setup failure; the creator closes its duplicate if
    startup fails. The worker takes ownership only after successful startup.
    Callers do not invoke this factory for dry runs or quiet executions.
    """
    ...

class SilentProgressSink:
    """Discard progress snapshots without touching the run or evidence."""

    def publish(self, snapshot: ProgressSnapshot, /) -> None: ...

class TerminalProgressSink:
    """Render bounded updates and offer them to a progress admission port."""

    admit: ProgressAdmission
    is_tty: bool
    runtime: Runtime
    interval_seconds: float

    def __init__(
        self,
        admit: ProgressAdmission,
        is_tty: bool,
        runtime: Runtime,
        interval_seconds: float,
        /,
    ) -> None: ...
    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Offer an update without treating admission as completed output.

        Routine updates use the injected monotonic clock and finite interval.
        Meaningful transitions are offered immediately. Dropped messages are
        not queued by the sink; unavailable output disables presentation.
        """
        ...
