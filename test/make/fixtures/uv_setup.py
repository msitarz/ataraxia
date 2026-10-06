#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Simulate offline environment setup while recording the external uv boundary."""

import json
import os
from pathlib import Path
import sys


def main() -> int:
    """Record setup requests, rejecting unusable cache or failed verification."""
    arguments = sys.argv[1:]
    names = (
        "UV_CACHE_DIR",
        "PREK_HOME",
        "UV_PROJECT_ENVIRONMENT",
        "VIRTUAL_ENV",
        "UV_OFFLINE",
        "UV_NO_SYNC",
    )
    environment = {name: os.environ.get(name) for name in names}
    with Path(os.environ["STUB_UV_LOG"]).open("a", encoding="utf-8") as log:
        log.write(json.dumps({"argv": arguments, "environment": environment}) + "\n")
    project = Path(os.environ["UV_PROJECT_ENVIRONMENT"])
    if "--check" in arguments:
        if os.environ.get("STUB_SETUP_FAIL_VERIFY") == "true":
            return 24
        return 0 if project.is_dir() else 23
    cache = Path(os.environ["UV_CACHE_DIR"])
    if not (cache / "ready").is_file():
        return 17
    project.mkdir(parents=True, exist_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
