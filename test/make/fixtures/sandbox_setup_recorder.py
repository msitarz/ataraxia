#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Record setup commands launched while creating a disposable sandbox."""

import json
import os
from pathlib import Path
import shutil
import sys

directory = Path.cwd()
if sys.argv[1:] not in (["setup"], ["verify-setup"]):
    executable = os.environ.get("REAL_MAKE_PATH") or shutil.which("make")
    if executable is None:
        raise SystemExit("real Make executable not configured")
    os.execv(executable, [executable, *sys.argv[1:]])

record = directory / ".sandbox-setup-log.jsonl"
environment = {
    key: os.environ.get(key)
    for key in (
        "UV_CACHE_DIR",
        "PREK_HOME",
        "UV_PROJECT_ENVIRONMENT",
        "HOME",
        "TMPDIR",
        "VIRTUAL_ENV",
    )
}
with record.open("a") as stream:
    stream.write(
        json.dumps({
            "argv": sys.argv[1:],
            "cwd": str(directory),
            "environment": environment,
        })
        + "\n"
    )
if directory.name == "failed" and sys.argv[1:] == ["setup"]:
    sys.stderr.write("simulated setup failure\n")
    raise SystemExit(17)
if directory.name == "verify-failed" and sys.argv[1:] == ["verify-setup"]:
    sys.stderr.write("simulated readiness failure\n")
    raise SystemExit(19)
