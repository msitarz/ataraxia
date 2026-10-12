#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Record external uv requests without executing the requested tool."""

import json
import os
from pathlib import Path
import subprocess
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
    if "ATARAXIA_COMMIT_SUBJECT" in os.environ:
        record["environment"].update({
            name: os.environ.get(name)
            for name in (
                "ATARAXIA_COMMIT_SUBJECT",
                "ATARAXIA_COMMIT_BODY",
                "MAKEFLAGS",
                "MAKEOVERRIDES",
            )
        })
    nested_exit = 0
    nested_stderr = ""
    if os.environ.get("STUB_NESTED_MAKE"):
        nested = subprocess.run(
            ["make", "--no-print-directory", "help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        nested_exit = nested.returncode
        nested_stderr = nested.stderr
        if "ATARAXIA_COMMIT_SUBJECT" in os.environ:
            record["environment"]["MAKE_NESTED_EXIT"] = str(nested.returncode)
    with Path(os.environ["STUB_UV_LOG"]).open("a", encoding="utf-8") as log:
        log.write(json.dumps(record) + "\n")
    if nested_exit != 0:
        sys.stderr.write(nested_stderr)
        return nested_exit
    sys.stdout.write(os.environ.get("STUB_UV_STDOUT", ""))
    sys.stderr.write(os.environ.get("STUB_UV_STDERR", ""))
    if os.environ.get("STUB_UV_FAIL_ARGS") == json.dumps(arguments):
        return int(os.environ["STUB_UV_EXIT"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
