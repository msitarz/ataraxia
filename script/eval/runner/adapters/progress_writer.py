# SPDX-License-Identifier: Apache-2.0
"""Best-effort bounded progress output on one owned daemon thread."""

from collections.abc import Callable
from contextlib import suppress
import os
import re
import threading
import time

from script.eval.runner.adapters.progress import Admission

MAX_MESSAGE_BYTES = 16 * 1024
PANEL_CONTROL_RESERVE = 128
WORKER_POLL_SECONDS = 0.01
PANEL_MIN_COLUMNS = 60
PANEL_HEIGHT_MARGIN = 2
_ANSI = re.compile(rb"\x1b\[[0-9;]*m")


class ProgressWriter:
    """Offer messages without waiting for a possibly blocked stderr write.

    One claimed message and one replaceable pending message are retained. The
    worker owns its descriptor until it exits; close never joins it.
    """

    def __init__(
        self,
        fd: int,
        write: Callable[[int, bytes], int],
        close_fd: Callable[[int], None],
        *,
        panel: bool = False,
        terminal_size: Callable[[int], os.terminal_size] = os.get_terminal_size,
    ) -> None:
        """Retain an already duplicated descriptor and explicit I/O leaves."""
        self._panel = panel
        self._terminal_size = terminal_size
        self._panel_size: os.terminal_size | None = None
        self._panel_rows = 0
        self._finishing = False
        self._done = threading.Event()
        self._fd = fd
        self._write = write
        self._close_fd = close_fd
        self._lock = threading.Lock()
        self._pending: tuple[bytes, bool] | None = None
        self._closed = False
        self._failed = False

    def __call__(self, text: str, /, *, important: bool = False) -> Admission:
        """Admit one message, replace pending output, or promptly drop it.

        Returns:
            Admission status, which does not indicate bytes were written.
        """
        if self._closed or self._failed or self._finishing:
            return "unavailable"
        if len(text) > MAX_MESSAGE_BYTES:
            return "dropped"
        data = text.encode("utf-8")
        if len(data) > MAX_MESSAGE_BYTES - (
            PANEL_CONTROL_RESERVE if self._panel else 0
        ) or not self._lock.acquire(blocking=False):
            return "dropped"
        try:
            if self._closed or self._failed or self._finishing:
                return "unavailable"
            if self._pending is not None and self._pending[1] and not important:
                return "dropped"
            self._pending = (data, important)
            return "accepted"
        finally:
            self._lock.release()

    def close(self) -> None:
        """Stop admission without waiting for I/O or joining the worker."""
        self._closed = True

    def finish(self) -> None:
        """Seal admission and let the worker drain its pending frame."""
        self._finishing = True

    @property
    def finished(self) -> bool:
        """Whether the worker has stopped and released its descriptor."""
        return self._done.is_set()

    def work(self) -> None:
        """Own the descriptor and write claimed messages until stopped."""
        try:
            self._work_loop()
        finally:
            self._failed = True
            with suppress(Exception):
                self._close_fd(self._fd)
            self._done.set()

    def _work_loop(self) -> None:
        """Claim pending messages without holding state locks across I/O."""
        while not self._closed:
            message = self._claim()
            if message is None:
                if self._finishing and self._drained():
                    return
                time.sleep(WORKER_POLL_SECONDS)
                continue
            message, size, rows = self._frame(message)
            try:
                count = self._write(self._fd, message)
            except Exception:
                self._failed = True
                return
            if count != len(message):
                self._failed = True
                return
            self._panel_size, self._panel_rows = size, rows

    def _drained(self) -> bool:
        """Check pending state without waiting on admission.

        Returns:
            Whether no pending frame remains.
        """
        if not self._lock.acquire(blocking=False):
            return False
        try:
            return self._pending is None
        finally:
            self._lock.release()

    def _frame(self, message: bytes) -> tuple[bytes, os.terminal_size | None, int]:
        """Prepare replacement only for a fully delivered, fitting previous panel.

        Returns:
            The write bytes and resulting panel geometry.
        """
        if not self._panel:
            return message, None, 0
        try:
            size = self._terminal_size(self._fd)
        except OSError:
            return message, None, 0
        lines = message.splitlines()
        fits = (
            size.columns >= PANEL_MIN_COLUMNS
            and len(lines) + PANEL_HEIGHT_MARGIN <= size.lines
            and all(len(_ANSI.sub(b"", line)) < size.columns for line in lines)
        )
        if not fits:
            return message, None, 0
        prefix = b""
        if size == self._panel_size and self._panel_rows:
            prefix = f"\x1b[{self._panel_rows}A\x1b[J".encode()
        return prefix + message, size, len(lines)

    def _claim(self) -> bytes | None:
        """Claim one pending message, or return promptly on contention.

        Returns:
            A claimed message, if one was pending before shutdown.
        """
        if not self._lock.acquire(blocking=False):
            return None
        try:
            if self._closed:
                return None
            pending, self._pending = self._pending, None
            return None if pending is None else pending[0]
        finally:
            self._lock.release()


def open_progress_writer(
    stderr_fd: int,
    /,
    *,
    duplicate: Callable[[int], int] = os.dup,
    write: Callable[[int, bytes], int] = os.write,
    close_fd: Callable[[int], None] = os.close,
    thread_factory: Callable[[Callable[[], None]], threading.Thread] | None = None,
    panel: bool = False,
    terminal_size: Callable[[int], os.terminal_size] = os.get_terminal_size,
) -> ProgressWriter | None:
    """Start one daemon worker with its own non-inheritable stderr duplicate.

    Returns:
        A writer, or None if an ordinary setup failure prevents presentation.
    """
    try:
        owned = duplicate(stderr_fd)
    except Exception:
        return None
    writer = ProgressWriter(
        owned, write, close_fd, panel=panel, terminal_size=terminal_size
    )
    handoff = _DescriptorHandoff(writer, owned, close_fd)
    return handoff.start(thread_factory or _thread)


class _DescriptorHandoff:
    """Transfer a duplicate to a started worker or revoke a failed start."""

    def __init__(
        self, writer: ProgressWriter, fd: int, close_fd: Callable[[int], None]
    ) -> None:
        self.writer = writer
        self.fd = fd
        self.close_fd = close_fd
        self.lock = threading.Lock()
        self.granted = False
        self.claimed = False

    def start(
        self, factory: Callable[[Callable[[], None]], threading.Thread]
    ) -> ProgressWriter | None:
        """Start a worker while retaining ownership until start settles.

        Returns:
            The writer on success, or None on an ordinary setup failure.
        """
        try:
            with self.lock:
                thread = factory(self.enter)
                thread.daemon = True
                thread.start()
                self.granted = True
        except BaseException as error:
            with self.lock:
                claimed = self.claimed
                self.granted = False
            if claimed:
                self.writer.close()
            else:
                with suppress(BaseException):
                    self.close_fd(self.fd)
            if isinstance(error, Exception):
                return None
            raise
        return self.writer

    def enter(self) -> None:
        """Claim ownership only after start succeeds, or leave revoked state."""
        with self.lock:
            if not self.granted:
                return
            self.claimed = True
        self.writer.work()


def _thread(target: Callable[[], None]) -> threading.Thread:
    """Create the one daemon thread for an owned progress writer.

    Returns:
        An unstarted daemon thread.
    """
    return threading.Thread(target=target, name="evaluation-progress", daemon=True)
