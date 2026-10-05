#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Record external uv requests without executing the requested tool."""

import json
import os
from pathlib import Path
import sys

ENVIRONMENT_NAMES = (
    "UV_OFFLINE",
    "UV_NO_SYNC",
    "UV_CACHE_DIR",
    "PREK_HOME",
    "UV_PROJECT_ENVIRONMENT",
    "VIRTUAL_ENV",
    "HOME",
    "TMPDIR",
)


def main() -> int:
    """Record one call and emit configured diagnostics and status."""
    arguments = sys.argv[1:]
    record = {
        "argv": arguments,
        "environment": {name: os.environ.get(name) for name in ENVIRONMENT_NAMES},
    }
    with Path(os.environ["STUB_UV_LOG"]).open("a", encoding="utf-8") as log:
        log.write(json.dumps(record) + "\n")
    sys.stdout.write(os.environ.get("STUB_UV_STDOUT", ""))
    sys.stderr.write(os.environ.get("STUB_UV_STDERR", ""))
    if os.environ.get("STUB_UV_FAIL_ARGS") == json.dumps(arguments):
        return int(os.environ["STUB_UV_EXIT"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
