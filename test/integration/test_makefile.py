# SPDX-License-Identifier: Apache-2.0
"""Check validation orchestration without installing tools or using the network."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def fake_uv_environment(tmp_path):
    """Return a fake uv executable environment and its captured-call log."""
    log = tmp_path / "uv-calls.jsonl"
    uv = tmp_path / "uv"
    uv.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "with open(os.environ['FAKE_UV_LOG'], 'a') as log:\n"
        "    log.write(json.dumps(sys.argv[1:]) + '\\n')\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    env = os.environ.copy()
    env.update(PATH=f"{tmp_path}:{env['PATH']}", FAKE_UV_LOG=str(log))
    env.pop("MAKEFLAGS", None)
    env.pop("MAKEOVERRIDES", None)
    env.pop("MFLAGS", None)
    env.pop("ARGS", None)
    env.pop("CLI_ARGS", None)
    return env, log


def run_make_with_fake_uv(tmp_path, *args):
    """Run Make against a fake uv executable and return output and calls."""
    env, log = fake_uv_environment(tmp_path)
    result = subprocess.run(
        ["make", *args], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30
    )
    calls = (
        [json.loads(line) for line in log.read_text().splitlines()]
        if log.exists()
        else []
    )
    return result, calls


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
    env.pop("MAKEFLAGS", None)
    env.pop("MAKEOVERRIDES", None)
    env.pop("MFLAGS", None)
    env.pop("ARGS", None)
    env.pop("CLI_ARGS", None)
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
    env.pop("MAKEFLAGS", None)
    env.pop("MAKEOVERRIDES", None)
    env.pop("MFLAGS", None)
    env.pop("ARGS", None)
    env.pop("CLI_ARGS", None)

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


@pytest.mark.parametrize(
    ("target", "args", "expected"),
    [
        ("lint", (), [["run", "ruff", "check", ".", "--fix"]]),
        (
            "lint",
            ("ARGS=src/feature.py",),
            [["run", "ruff", "check", "src/feature.py", "--fix"]],
        ),
        (
            "lint-check",
            ("ARGS=src/feature.py src/provider.py",),
            [["run", "ruff", "check", "src/feature.py", "src/provider.py"]],
        ),
        ("format", (), [["run", "ruff", "format", "."]]),
        (
            "format",
            ("ARGS=src/feature.py",),
            [["run", "ruff", "format", "src/feature.py"]],
        ),
        (
            "format-check",
            ("ARGS=src/feature.py",),
            [["run", "ruff", "format", "--check", "src/feature.py"]],
        ),
        ("test", (), [["run", "pytest", "--cov"]]),
        (
            "test",
            ("ARGS=test/unit/test_cli.py",),
            [["run", "pytest", "test/unit/test_cli.py"]],
        ),
        (
            "typecheck",
            (),
            [
                ["run", "pyrefly", "check"],
                [
                    "run",
                    "pyrefly",
                    "check",
                    "--expectations",
                    "test/typecheck/compute_contracts.py",
                ],
            ],
        ),
        (
            "typecheck",
            ("ARGS=src/ataraxia/feature.py",),
            [["run", "pyrefly", "check", "src/ataraxia/feature.py"]],
        ),
        (
            "typecheck-expectations",
            ("ARGS=test/typecheck/compute_contracts.py",),
            [
                [
                    "run",
                    "pyrefly",
                    "check",
                    "--expectations",
                    "test/typecheck/compute_contracts.py",
                ]
            ],
        ),
    ],
)
def test_make_tool_targets_preserve_defaults_and_route_selectors(
    tmp_path, target, args, expected
):
    result, calls = run_make_with_fake_uv(tmp_path, target, *args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == expected


def test_markdown_targets_pass_selected_paths_to_both_checkers(tmp_path):
    result, calls = run_make_with_fake_uv(
        tmp_path, "doc-check", "ARGS=doc/acceptance-tracing.md"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [
        ["run", "rumdl", "check", "doc/acceptance-tracing.md", "."],
        ["run", "rumdl", "fmt", "--check", "doc/acceptance-tracing.md"],
    ]


def test_markdown_format_target_passes_selected_paths(tmp_path):
    result, calls = run_make_with_fake_uv(
        tmp_path, "doc-format", "ARGS=doc/acceptance-tracing.md"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [["run", "rumdl", "fmt", "doc/acceptance-tracing.md"]]


def test_make_selectors_quote_shell_metacharacters(tmp_path):
    marker = tmp_path / "should-not-be-created"
    selector = f"src/example.py; touch {marker}"

    result, calls = run_make_with_fake_uv(tmp_path, "lint-check", f"ARGS={selector}")

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [["run", "ruff", "check", "src/example.py;", "touch", str(marker)]]
    assert not marker.exists()


def test_make_selectors_quote_single_quotes(tmp_path):
    result, calls = run_make_with_fake_uv(
        tmp_path, "format-check", "ARGS=src/example's.py"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [["run", "ruff", "format", "--check", "src/example's.py"]]


def test_path_selectors_reject_tool_options(tmp_path):
    result, calls = run_make_with_fake_uv(tmp_path, "lint-check", "ARGS=--fix")

    assert result.returncode != 0
    assert "ARGS accepts paths, not options" in result.stderr
    assert calls == []


def test_run_target_routes_project_cli_arguments(tmp_path):
    result, calls = run_make_with_fake_uv(
        tmp_path,
        "run",
        "CLI_ARGS=--sink example/crossover.py "
        "--shards-dir sample --output results.json",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [
        [
            "run",
            "ataraxia",
            "--sink",
            "example/crossover.py",
            "--shards-dir",
            "sample",
            "--output",
            "results.json",
        ]
    ]


def test_run_target_requires_cli_arguments(tmp_path):
    result, calls = run_make_with_fake_uv(tmp_path, "run")

    assert result.returncode != 0
    assert "CLI_ARGS" in result.stderr
    assert calls == []


def test_cli_arguments_quote_shell_metacharacters(tmp_path):
    marker = tmp_path / "should-not-be-created"
    cli_args = f"--option value; touch {marker}"

    result, calls = run_make_with_fake_uv(tmp_path, "run", f"CLI_ARGS={cli_args}")

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [["run", "ataraxia", "--option", "value;", "touch", str(marker)]]
    assert not marker.exists()


def test_dependency_lock_target_uses_uv_lock(tmp_path):
    result, calls = run_make_with_fake_uv(tmp_path, "deps-lock")

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [["lock"]]


def test_full_verification_ignores_targeted_test_selector(tmp_path):
    result, calls = run_make_with_fake_uv(
        tmp_path, "verify-test", "ARGS=test/unit/test_cli.py"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [["run", "pytest", "--cov"]]


def test_full_static_verification_ignores_targeted_path_selector(tmp_path):
    result, calls = run_make_with_fake_uv(
        tmp_path, "verify-check", "ARGS=src/ataraxia/feature.py"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert ["run", "ruff", "check", "."] in calls
    assert ["run", "ruff", "format", "--check", "."] in calls
    assert ["run", "rumdl", "check", "."] in calls
    assert ["run", "rumdl", "fmt", "--check", "."] in calls
    assert ["run", "pyrefly", "check"] in calls
    assert not any("src/ataraxia/feature.py" in command for command in calls)


def test_full_example_verification_ignores_targeted_path_selector(tmp_path):
    result, calls = run_make_with_fake_uv(
        tmp_path, "verify-examples", "ARGS=example/crossover.py"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [["run", "pytest", "example/"]]
