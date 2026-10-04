# SPDX-License-Identifier: Apache-2.0
"""Exercise registry selection's actual Make argument boundary offline."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def proxy_environment(tmp_path):
    """Copy the Make/CLI boundary and install a local uv argument proxy."""
    shutil.copyfile(ROOT / "Makefile", tmp_path / "Makefile")
    (tmp_path / "script").mkdir()
    shutil.copyfile(
        ROOT / "script/registry_selection.py", tmp_path / "script/registry_selection.py"
    )
    proxy = tmp_path / "uv"
    proxy.write_text(
        f"#!{sys.executable}\n"
        "import json, os, subprocess, sys\n"
        "open('argv.json', 'w').write(json.dumps(sys.argv[1:]))\n"
        "if os.getenv('RUN_SELECTION'):\n"
        "    sys.exit(subprocess.call([sys.executable, *sys.argv[3:]]))\n"
    )
    proxy.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    for name in (
        "MAKEFLAGS",
        "MAKEOVERRIDES",
        "MFLAGS",
        "CACHE",
        "RECORD",
        "PREPARATION_SHA256",
        "DESTINATION",
    ):
        env.pop(name, None)
    return env


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
def test_make_registry_arguments_are_literal(tmp_path):
    """AC-2: Make and shell metacharacters remain literal argv without execution."""
    env = proxy_environment(tmp_path)
    literal = (
        "a space's $(shell touch MAKE_PWNED)$(touch SHELL_PWNED)`touch TICK_PWNED`"
    )
    variables = ["CACHE", "RECORD", "PREPARATION_SHA256", "DESTINATION"]
    values = [f"{literal}-{name}" for name in variables]
    result = subprocess.run(
        [
            "make",
            "registry-select",
            *[f"{name}={value}" for name, value in zip(variables, values, strict=True)],
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads((tmp_path / "argv.json").read_text()) == [
        "run",
        "python",
        "script/registry_selection.py",
        "--cache",
        values[0],
        "--record",
        values[1],
        "--expected",
        values[2],
        "--destination",
        values[3],
    ]
    assert not any(
        (tmp_path / name).exists()
        for name in ("MAKE_PWNED", "SHELL_PWNED", "TICK_PWNED")
    )


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
def test_make_missing_arguments_fail_before_destination_creation(tmp_path):
    """AC-2: omitted Make inputs reach a recoverable CLI usage failure offline."""
    env = proxy_environment(tmp_path)
    env["RUN_SELECTION"] = "1"
    destination = tmp_path / "result"
    result = subprocess.run(
        ["make", "registry-select", f"DESTINATION={destination}"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "must be nonempty" in result.stderr
    assert not destination.exists()
