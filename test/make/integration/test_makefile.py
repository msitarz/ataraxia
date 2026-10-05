# SPDX-License-Identifier: Apache-2.0
"""Check local and CI orchestration without installing tools or using the network."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]


def expected_size_advisory(*paths: str) -> list[str]:
    """Return the Make lint target's advisory Ruff invocation."""
    return [
        "run",
        "ruff",
        "check",
        "--select",
        "too-many-statements",
        "--config",
        "lint.pylint.max-statements=25",
        "--exit-zero",
        *paths,
    ]


def fake_uv_environment(tmp_path):
    """Return a fake uv executable environment and its captured-call log."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    log = tmp_path / "uv-calls.jsonl"
    uv = tmp_path / "uv"
    uv.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "with open(os.environ['FAKE_UV_LOG'], 'a') as log:\n"
        "    log.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "with open(os.environ['FAKE_UV_ENV_LOG'], 'a') as log:\n"
        "    log.write(json.dumps([os.getenv('UV_OFFLINE'), "
        "os.getenv('UV_NO_SYNC')]) + '\\n')\n"
        "if '--exit-zero' in sys.argv:\n"
        "    sys.exit(int(os.getenv('FAKE_UV_ADVISORY_EXIT', '0')))\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    env = os.environ.copy()
    env.update(
        PATH=f"{tmp_path}:{env['PATH']}",
        FAKE_UV_LOG=str(log),
        FAKE_UV_ENV_LOG=str(tmp_path / "uv-env-calls.jsonl"),
    )
    env.pop("MAKEFLAGS", None)
    env.pop("MAKEOVERRIDES", None)
    env.pop("MFLAGS", None)
    env.pop("ARGS", None)
    env.pop("CLI_ARGS", None)
    return env, log


def run_make_with_fake_uv(tmp_path, *args, advisory_exit=0):
    """Run Make against a fake uv executable and return output and calls."""
    env, log = fake_uv_environment(tmp_path)
    env["FAKE_UV_ADVISORY_EXIT"] = str(advisory_exit)
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
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/ci-preparation/README.md",
    ac="AC-3",
)
def test_check_order_and_offline_environment(tmp_path, target, failure, expected):
    """AC-3: Prepared checks run offline, check stale envs, and audit CI.

    Prepared offline checks remain network-free, reject a missing or
    stale environment, and exercise the installed package outside the
    worktree. Dependency synchronization stays locked and audit remains
    required by full CI.
    """
    log = tmp_path / "calls.jsonl"
    uv = tmp_path / "uv"
    uv.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "args = sys.argv[1:]\n"
        "with open(os.environ['CHECK_LOG'], 'a') as log:\n"
        "    log.write(json.dumps([args, os.getenv('UV_OFFLINE'), "
        "os.getenv('UV_NO_SYNC')]) + '\\n')\n"
        "failure = os.environ['CHECK_FAILURE']\n"
        "sys.exit(1 if (failure == 'audit' and args[0] == 'audit') or "
        "(failure == 'sync-check' and '--check' in args) else 0)\n"
    )
    uv.chmod(0o755)
    env = os.environ.copy()
    env.update(
        PATH=f"{tmp_path}:{env['PATH']}",
        CHECK_LOG=str(log),
        CHECK_FAILURE=failure,
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
    local = calls if target == "verify" else calls[2:-1]
    assert all(offline == "true" and no_sync == "true" for _, offline, no_sync in local)
    if target == "ci":
        assert commands[1] == ["run", "--no-sync", "prek", "prepare-hooks"] and (
            commands[-1][0] == "audit"
        )
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
        "with open(os.environ['CHECK_LOG'], 'a') as log:\n"
        "    log.write(json.dumps([sys.argv[1:], os.getenv('UV_OFFLINE'), "
        "os.getenv('UV_NO_SYNC')]) + '\\n')\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    env = os.environ.copy()
    env.update(PATH=f"{tmp_path}:{env['PATH']}", CHECK_LOG=str(log))
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
        (
            "lint",
            (),
            [
                ["run", "ruff", "check", ".", "--fix"],
                expected_size_advisory("."),
            ],
        ),
        (
            "lint",
            ("ARGS=src/feature.py",),
            [
                ["run", "ruff", "check", "src/feature.py", "--fix"],
                expected_size_advisory("src/feature.py"),
            ],
        ),
        (
            "lint-check",
            ("ARGS=src/feature.py src/provider.py",),
            [
                ["run", "ruff", "check", "src/feature.py", "src/provider.py"],
                expected_size_advisory("src/feature.py", "src/provider.py"),
            ],
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
            ("ARGS=test/ataraxia/unit/test_cli.py",),
            [["run", "pytest", "test/ataraxia/unit/test_cli.py"]],
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
                    "test/ataraxia/typecheck/compute_contracts.py",
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
            ("ARGS=test/ataraxia/typecheck/compute_contracts.py",),
            [
                [
                    "run",
                    "pyrefly",
                    "check",
                    "--expectations",
                    "test/ataraxia/typecheck/compute_contracts.py",
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


def test_lint_target_does_not_suppress_advisory_tool_failures(tmp_path):
    result, calls = run_make_with_fake_uv(tmp_path, "lint-check", advisory_exit=2)

    assert result.returncode != 0
    assert len(calls) == 2
    assert "--exit-zero" in calls[1]


def test_markdown_targets_pass_selected_paths_to_both_checkers(tmp_path):
    result, calls = run_make_with_fake_uv(
        tmp_path, "doc-check", "ARGS=doc/acceptance-tracing.md"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [
        ["run", "rumdl", "check", "doc/acceptance-tracing.md", "."],
        ["run", "rumdl", "fmt", "--check", "doc/acceptance-tracing.md"],
    ]


def make_worktree_fixture(tmp_path):
    """Create a disposable master repository and an offline fake uv."""
    repo = tmp_path / "source"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-b", "master"], cwd=repo, check=True, capture_output=True
    )
    (repo / "Makefile").write_bytes((ROOT / "Makefile").read_bytes())
    subprocess.run(["git", "add", "Makefile"], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-m",
            "init",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    uv = bin_dir / "uv"
    uv.write_text(
        f"#!{sys.executable}\n"
        "import json, os, pathlib, sys\n"
        "args = sys.argv[1:]\n"
        "record = {\n"
        "  'args': args, 'cache': os.getenv('UV_CACHE_DIR'),\n"
        "  'prek': os.getenv('PREK_HOME'),\n"
        "  'project': os.getenv('UV_PROJECT_ENVIRONMENT'),\n"
        "  'virtual': os.getenv('VIRTUAL_ENV'),\n"
        "  'no_sync': os.getenv('UV_NO_SYNC'),\n"
        "  'offline': os.getenv('UV_OFFLINE'),\n"
        "}\n"
        "with open(os.environ['WORKTREE_UV_LOG'], 'a') as log:\n"
        "    log.write(json.dumps(record) + '\\n')\n"
        "project = pathlib.Path(record['project'])\n"
        "if '--check' in args:\n"
        "    if os.getenv('WORKTREE_UV_FAIL_VERIFY') == 'true':\n"
        "        sys.exit(24)\n"
        "    sys.exit(0 if project.is_dir() else 23)\n"
        "cache = pathlib.Path(record['cache'])\n"
        "if not (cache / 'ready').exists():\n"
        "    sys.exit(17)\n"
        "project.mkdir(parents=True, exist_ok=True)\n"
    )
    uv.chmod(0o755)
    env = os.environ.copy()
    env.update(
        PATH=f"{bin_dir}:{env['PATH']}",
        WORKTREE_UV_LOG=str(tmp_path / "uv-worktree.jsonl"),
        UV_CACHE_DIR=str(repo / ".cache" / "uv"),
        PREK_HOME=str(repo / ".cache" / "prek"),
        UV_PROJECT_ENVIRONMENT=str(repo / ".venv"),
        VIRTUAL_ENV=str(repo / ".venv"),
        UV_NO_SYNC="true",
    )
    for name in ("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "ARGS", "CLI_ARGS"):
        env.pop(name, None)
    return repo, env


def assert_worktree_uv_routing(env, destination):
    """Verify both setup phases use only destination-local environment paths."""
    calls = [
        json.loads(line)
        for line in Path(env["WORKTREE_UV_LOG"]).read_text().splitlines()
    ]
    assert [call["args"] for call in calls] == [
        ["sync", "--locked", "--group", "dev"],
        ["sync", "--locked", "--group", "dev", "--check", "--offline"],
    ]
    for call in calls:
        assert call["cache"] == str(destination / ".cache/uv")
        assert call["prek"] == str(destination / ".cache/prek")
        assert call["project"] == str(destination / ".venv")
        assert call["virtual"] is None
        assert call["offline"] == "true"
    assert [call["no_sync"] for call in calls] == ["false", "true"]


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/workspace-preparation/README.md",
    ac="AC-1",
)
def test_worktree_create_copies_cache_and_routes_isolated_offline_setup(tmp_path):
    """AC-1: A new worktree gets its own cache and verified environment."""
    repo, env = make_worktree_fixture(tmp_path)
    source_cache = repo / ".cache"
    (source_cache / "uv").mkdir(parents=True)
    (source_cache / "prek").mkdir()
    (source_cache / "uv" / "ready").write_text("cached")
    (source_cache / "prek" / "example").write_text("cached")
    (repo / ".venv").mkdir()
    (repo / ".venv" / "parent-only").write_text("do not copy")
    destination = tmp_path / "agent's worktree;touch PWNED"

    result = subprocess.run(
        [
            "make",
            "worktree-create",
            f"WORKTREE={destination}",
            "BRANCH=work/example",
            f"UV_CACHE_DIR={repo / 'parent-cache'}",
            f"PREK_HOME={repo / 'parent-prek'}",
            f"UV_PROJECT_ENVIRONMENT={repo / 'parent-venv'}",
            "UV_NO_SYNC=true",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Worktree ready" in result.stdout
    assert (destination / ".cache/uv/ready").exists()
    assert (destination / ".cache/prek/example").exists()
    assert not (repo / "PWNED").exists()
    assert not (destination / ".venv/parent-only").exists()
    assert (destination / ".venv").is_dir()
    assert_worktree_uv_routing(env, destination)


@pytest.mark.parametrize("cache_kind", ["absent", "incomplete"])
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/workspace-preparation/README.md",
    ac="AC-1",
)
def test_worktree_create_preserves_worktree_when_offline_cache_is_unusable(
    tmp_path, cache_kind
):
    """AC-1: Missing or incomplete offline caches leave a recoverable worktree."""
    repo, env = make_worktree_fixture(tmp_path)
    if cache_kind == "incomplete":
        (repo / ".cache/uv").mkdir(parents=True)
        (repo / ".cache/uv/partial").write_text("partial")
    destination = tmp_path / "failed-worktree"

    result = subprocess.run(
        ["make", "worktree-create", f"WORKTREE={destination}", "BRANCH=work/failed"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode != 0
    assert destination.is_dir()
    assert "worktree retained" in result.stderr
    assert "make ci-setup UV_OFFLINE=true" in result.stderr
    assert not (destination / ".venv").exists()
    if cache_kind == "incomplete":
        assert (destination / ".cache/uv/partial").exists()


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/workspace-preparation/README.md",
    ac="AC-1",
)
def test_worktree_create_preserves_worktree_when_environment_check_fails(
    tmp_path,
):
    """AC-1: A failed post-setup check does not remove the prepared worktree."""
    repo, env = make_worktree_fixture(tmp_path)
    env["WORKTREE_UV_FAIL_VERIFY"] = "true"
    cache = repo / ".cache/uv"
    cache.mkdir(parents=True)
    (cache / "ready").write_text("cached")
    destination = tmp_path / "check-failed"

    result = subprocess.run(
        ["make", "worktree-create", f"WORKTREE={destination}", "BRANCH=work/verify"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode != 0
    assert destination.is_dir()
    assert (destination / ".venv").is_dir()
    assert "Environment check failed" in result.stderr
    assert "worktree retained" in result.stderr


@pytest.mark.parametrize("conflict", ["destination", "branch"])
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/workspace-preparation/README.md",
    ac="AC-1",
)
def test_worktree_create_rejects_conflicts_without_cleanup(tmp_path, conflict):
    """AC-1: Existing destination or branch is rejected before mutation."""
    repo, env = make_worktree_fixture(tmp_path)
    destination = tmp_path / "conflict"
    if conflict == "destination":
        destination.mkdir()
        (destination / "keep").write_text("preserve")
    else:
        subprocess.run(["git", "branch", "work/existing"], cwd=repo, check=True)
    branch_name = "work/example" if conflict == "destination" else "work/existing"

    result = subprocess.run(
        [
            "make",
            "worktree-create",
            f"WORKTREE={destination}",
            f"BRANCH={branch_name}",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode != 0
    if conflict == "destination":
        assert (destination / "keep").read_text() == "preserve"
        assert "destination already exists" in result.stderr
    else:
        assert not destination.exists()
        assert "Branch already exists" in result.stderr


def test_markdown_format_target_passes_selected_paths(tmp_path):
    result, calls = run_make_with_fake_uv(
        tmp_path, "doc-format", "ARGS=doc/acceptance-tracing.md"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [
        [
            "run",
            "rumdl",
            "fmt",
            "--config",
            "pyproject.toml",
            "doc/acceptance-tracing.md",
        ]
    ]


def test_make_selectors_quote_shell_metacharacters(tmp_path):
    marker = tmp_path / "should-not-be-created"
    selector = f"src/example.py; touch {marker}"

    result, calls = run_make_with_fake_uv(tmp_path, "lint-check", f"ARGS={selector}")

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [
        ["run", "ruff", "check", "src/example.py;", "touch", str(marker)],
        expected_size_advisory("src/example.py;", "touch", str(marker)),
    ]
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


def test_full_checks_ignores_targeted_test_selector(tmp_path):
    result, calls = run_make_with_fake_uv(
        tmp_path, "verify-test", "ARGS=test/ataraxia/unit/test_cli.py"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [["run", "pytest", "--cov"]]


def test_full_static_checks_ignores_targeted_path_selector(tmp_path):
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


def test_full_example_checks_ignores_targeted_path_selector(tmp_path):
    result, calls = run_make_with_fake_uv(
        tmp_path, "verify-examples", "ARGS=example/crossover.py"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [["run", "pytest", "example/"]]


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/ci-preparation/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/ci-preparation/README.md",
    ac="AC-3",
)
def test_ci_preparation_is_allocated_to_its_consumers(tmp_path):
    """AC-2 and AC-3: CI setup and offline checks contracts.

    Each CI target prepares what its checks require, and missing required
    environments fail clearly. `make setup` still prepares hooks and build
    tooling for subsequent offline checks.

    Prepared offline checks remain network-free, reject a missing or
    stale environment, and exercise the installed package outside the
    worktree. Dependency synchronization stays locked and audit remains
    required by full CI.

    This fake-uv test checks Make routing and environment flags, not actual
    network behavior.
    """
    result, calls = run_make_with_fake_uv(tmp_path / "ci-setup", "ci-setup")

    assert (result.returncode, calls) == (
        0,
        [["sync", "--locked", "--group", "dev"]],
    )

    result, calls = run_make_with_fake_uv(tmp_path / "ci-test", "ci-test")

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [
        ["sync", "--locked", "--group", "dev"],
        ["run", "pytest", "--cov"],
    ]

    result, calls = run_make_with_fake_uv(tmp_path / "ci-examples", "ci-examples")

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [
        ["sync", "--locked", "--group", "dev"],
        ["run", "pytest", "example/"],
    ]

    result, calls = run_make_with_fake_uv(tmp_path / "setup", "setup")

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [
        ["sync", "--locked", "--group", "dev"],
        [
            "run",
            "--no-sync",
            "prek",
            "prepare-hooks",
        ],
        [
            "run",
            "--no-sync",
            "prek",
            "install",
            "--hook-type",
            "pre-commit",
            "--hook-type",
            "commit-msg",
        ],
        ["build", "--wheel", "--out-dir", ".cache/build"],
    ]

    package_dir = tmp_path / "ci-package"
    env, log = fake_uv_environment(package_dir)
    env.pop("UV_OFFLINE", None)
    result = subprocess.run(
        ["make", "ci-package"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    env_calls = [
        json.loads(line)
        for line in (package_dir / "uv-env-calls.jsonl").read_text().splitlines()
    ]
    assert calls == [
        ["python", "install"],
        ["run", "python", "script/smoke_installed_package.py"],
    ]
    assert env_calls == [[None, "true"], ["true", "true"]]

    result, calls = run_make_with_fake_uv(tmp_path / "ci-check", "ci-check")

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls[:2] == [
        ["sync", "--locked", "--group", "dev"],
        ["run", "--no-sync", "prek", "prepare-hooks"],
    ]
    assert calls[-1] == ["audit", "--frozen", "--preview-features", "audit"]
