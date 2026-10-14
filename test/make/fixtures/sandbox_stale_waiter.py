# SPDX-License-Identifier: Apache-2.0
"""Signal after a generation snapshot, at the external lock syscall."""

import fcntl
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def main() -> None:
    from script import sandbox

    real_flock = fcntl.flock

    def signaled_flock(descriptor: int, operation: int) -> None:
        if operation == fcntl.LOCK_EX:
            sys.stdout.write("captured\n")
            sys.stdout.flush()
        real_flock(descriptor, operation)

    with (
        patch.object(fcntl, "flock", signaled_flock),
        sandbox.locked_sandbox(Path(sys.argv[1]), sys.argv[2], sys.argv[3]),
    ):
        raise AssertionError("stale waiter unexpectedly acquired the recreated name")


if __name__ == "__main__":
    main()
