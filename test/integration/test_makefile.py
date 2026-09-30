# SPDX-License-Identifier: Apache-2.0
"""Check validation orchestration without installing tools or using the network."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("target", "failure", "expected"),
    [("verify", "", 0), ("verify", "sync-check", 2), ("ci", "audit", 2)],
)
def test_validation_order_and_offline_environment(tmp_path, target, failure, expected):
    log = tmp_path / "calls.jsonl"
    uv = tmp_path / "uv"
    uv.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "args = sys.argv[1:]\n"
        "with open(os.environ['VALIDATION_LOG'], 'a') as log:\n"
        "    log.write(json.dumps([args, os.getenv('UV_OFFLINE'), "
        "os.getenv('UV_NO_SYNC')]) + '\\n')\n"
        "failure = os.environ['VALIDATION_FAILURE']\n"
        "sys.exit(1 if (failure == 'audit' and args[0] == 'audit') or "
        "(failure == 'sync-check' and '--check' in args) else 0)\n"
    )
    uv.chmod(0o755)
    env = os.environ.copy()
    env.update(
        PATH=f"{tmp_path}:{env['PATH']}",
        VALIDATION_LOG=str(log),
        VALIDATION_FAILURE=failure,
    )
    env.pop("UV_OFFLINE", None)
    result = subprocess.run(
        ["make", target], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == expected, result.stdout + result.stderr
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    commands = [call[0] for call in calls]
    if failure == "sync-check":
        assert len(commands) == 1
        return
    assert ["run", "ruff", "check", "."] in commands
    assert ["run", "tach", "check"] in commands
    assert ["run", "pytest", "--cov"] in commands
    assert ["run", "pytest", "example/"] in commands
    assert ["run", "python", "script/smoke_installed_package.py"] in commands
    local = calls if target == "verify" else calls[3:-1]
    assert all(offline == "true" and no_sync == "true" for _, offline, no_sync in local)
    if target == "ci":
        assert commands[-1][0] == "audit"
        assert calls[-1][1] is None
    else:
        assert not any(command[0] == "audit" for command in commands)
        assert not any("prepare-hooks" in command for command in commands)


def test_local_and_ci_checks_use_the_same_read_only_doc_target(tmp_path):
    log = tmp_path / "calls.jsonl"
    uv = tmp_path / "uv"
    uv.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "with open(os.environ['VALIDATION_LOG'], 'a') as log:\n"
        "    log.write(json.dumps([sys.argv[1:], os.getenv('UV_OFFLINE'), "
        "os.getenv('UV_NO_SYNC')]) + '\\n')\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    env = os.environ.copy()
    env.update(PATH=f"{tmp_path}:{env['PATH']}", VALIDATION_LOG=str(log))
    env.pop("UV_OFFLINE", None)
    env.pop("UV_NO_SYNC", None)

    expected_doc_commands = [
        ["run", "rumdl", "check", "."],
        ["run", "rumdl", "fmt", "--check", "."],
    ]
    for target in ("verify-check", "ci-check"):
        log.write_text("", encoding="utf-8")
        result = subprocess.run(
            ["make", target],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr

        calls = [json.loads(line) for line in log.read_text().splitlines()]
        doc_calls = [call for call in calls if call[0][:2] == ["run", "rumdl"]]
        assert [call[0] for call in doc_calls] == expected_doc_commands
        assert all(
            offline == "true" and no_sync == "true" for _, offline, no_sync in doc_calls
        )
        assert not any(
            call[0][:3] == ["run", "rumdl", "fmt"] and "--check" not in call[0]
            for call in calls
        )
