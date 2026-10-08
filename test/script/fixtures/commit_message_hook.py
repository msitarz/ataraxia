#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Executable Git hook fixture that forwards to the real message checker."""

import os
import subprocess
import sys

TIMEOUT_SECONDS = 30


def main() -> int:
    """Run the supplied checker with the supplied interpreter and message path."""
    if len(sys.argv) != 2:
        return 2
    result = subprocess.run(
        [
            os.environ["ATARAXIA_COMMIT_MESSAGE_PYTHON"],
            os.environ["ATARAXIA_COMMIT_MESSAGE_CHECKER"],
            sys.argv[1],
        ],
        check=False,
        timeout=TIMEOUT_SECONDS,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
