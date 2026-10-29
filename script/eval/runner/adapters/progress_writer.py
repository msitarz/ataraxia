# SPDX-License-Identifier: Apache-2.0
"""Best-effort bounded progress output on one owned daemon thread."""

from collections.abc import Callable
from contextlib import suppress
import os
import threading
import time

from script.eval.runner.adapters.progress import Admission

MAX_MESSAGE_BYTES = 16 * 1024


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
    ) -> None:
        """Retain an already duplicated descriptor and explicit I/O leaves."""
        self._fd = fd
        self._write = write
        self._close_fd = close_fd
        self._lock = threading.Lock()
        self._pending: bytes | None = None
        self._closed = False
        self._failed = False

    def __call__(self, text: str, /) -> Admission:
        """Admit one message, replace pending output, or promptly drop it.

        Returns:
            Admission status, which does not indicate bytes were written.
        """
        if self._closed or self._failed:
            return "unavailable"
        if len(text) > MAX_MESSAGE_BYTES:
            return "dropped"
        data = text.encode("utf-8")
        if len(data) > MAX_MESSAGE_BYTES or not self._lock.acquire(blocking=False):
            return "dropped"
        try:
            if self._closed or self._failed:
                return "unavailable"
            self._pending = data
            return "accepted"
        finally:
            self._lock.release()

    def close(self) -> None:
        """Stop admission without waiting for I/O or joining the worker."""
        self._closed = True

    def work(self) -> None:
        """Own the descriptor and write claimed messages until stopped."""
        try:
            self._work_loop()
        finally:
            with suppress(Exception):
                self._close_fd(self._fd)

    def _work_loop(self) -> None:
        """Claim pending messages without holding state locks across I/O."""
        while not self._closed:
            message = self._claim()
            if message is None:
                time.sleep(0.01)
                continue
            try:
                count = self._write(self._fd, message)
            except Exception:
                self._failed = True
                return
            if count != len(message):
                self._failed = True
                return

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
            message, self._pending = self._pending, None
            return message
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
) -> ProgressWriter | None:
    """Start one daemon worker with its own non-inheritable stderr duplicate.

    Returns:
        A writer, or None if an ordinary setup failure prevents presentation.
    """
    try:
        owned = duplicate(stderr_fd)
    except OSError:
        return None
    writer = ProgressWriter(owned, write, close_fd)
    thread: threading.Thread | None = None
    try:
        thread = (thread_factory or _thread)(writer.work)
        thread.daemon = True
        thread.start()
    except Exception:
        if thread is not None and thread.ident is not None:
            writer.close()
        else:
            with suppress(Exception):
                close_fd(owned)
        return None
    return writer


def _thread(target: Callable[[], None]) -> threading.Thread:
    """Create the one daemon thread for an owned progress writer.

    Returns:
        An unstarted daemon thread.
    """
    return threading.Thread(target=target, name="evaluation-progress", daemon=True)
