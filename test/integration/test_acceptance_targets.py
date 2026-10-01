# SPDX-License-Identifier: Apache-2.0
"""Verify Make acceptance targets dispatch validated selection inputs."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORK = (
    "doc/feat/reviewable-workflow-v2/validation/docs-checks/"
    "acceptance-traceability/coverage-checker/README.md"
)


@pytest.mark.parametrize(
    ("target", "ac", "action"),
    [("ac-collect", "", "collect"), ("ac-test", "AC-8", "test")],
)
def test_make_acceptance_targets_dispatch_work_and_criterion(
    tmp_path, target, ac, action
):
    log = tmp_path / "calls.json"
    uv = tmp_path / "uv"
    uv.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "with open(os.environ['ACCEPTANCE_TARGET_LOG'], 'w') as log:\n"
        "    json.dump([sys.argv[1:], os.getenv('WORK'), os.getenv('AC')], log)\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    env = os.environ.copy()
    env.update(
        PATH=f"{tmp_path}:{env['PATH']}",
        ACCEPTANCE_TARGET_LOG=str(log),
    )

    args = ["make", target, f"WORK={WORK}"]
    if ac:
        args.append(f"AC={ac}")
    result = subprocess.run(
        args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=30
    )

    assert result.returncode == 0, result.stdout + result.stderr
    command, received_work, received_ac = json.loads(log.read_text(encoding="utf-8"))
    assert command == ["run", "python", "script/acceptance_tests.py", action]
    assert received_work == WORK
    assert received_ac == ac or received_ac is None
