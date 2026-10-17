# SPDX-License-Identifier: Apache-2.0
"""Check preparation allocation through real Make with external uv recorded."""

from pathlib import Path

import pytest

from test.make.support import MakeSandbox, make_sandbox
from test.make.worktree_support import creation_repository


@pytest.fixture
def sandbox(tmp_path: Path) -> MakeSandbox:
    """Provide a fresh isolated Make arrangement."""
    return make_sandbox(tmp_path)


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("ci-setup", [("sync", "--locked", "--group", "dev")]),
        (
            "ci-test",
            [
                ("sync", "--locked", "--group", "dev"),
                ("sync", "--locked", "--group", "dev", "--check", "--offline"),
                ("run", "pytest", "--cov"),
            ],
        ),
        (
            "ci-examples",
            [("sync", "--locked", "--group", "dev"), ("run", "pytest", "example/")],
        ),
    ],
    ids=["dependencies-only", "prepare-before-tests", "prepare-before-examples"],
)
def test_ci_targets_prepare_dependencies_before_their_consumer(
    sandbox: MakeSandbox,
    target: str,
    expected: list[tuple[str, ...]],
) -> None:
    """AC-1: Given each preparation target, real Make requests only its
    required preparation and subsequent consumers through fake uv; setup requests
    hooks/build, package requests Python preparation then offline smoke routing,
    and ci-check prepares hooks before checks and audit.

    AC-2: Each CI target prepares what its checks require, and missing required
    environments fail clearly. `make setup` still prepares hooks and build
    tooling for subsequent offline checks.

    AC-3: Prepared offline checks remain network-free, reject a missing or
    stale environment, and exercise the installed package outside the
    worktree. Dependency synchronization stays locked and audit remains
    required by full CI.

    This case covers dependency and test/example routing/flags only. It does not cover
    actual installs, network isolation, stale environments, or installed-package
    execution.
    """
    # Given: the sandbox fixture supplies the disposable environment.

    # When
    result = sandbox.run(target)

    # Then
    assert result.exit_code == 0, result.output
    assert [call.argv for call in result.calls] == expected


def test_setup_prepares_hooks_and_wheel_after_dependencies(tmp_path: Path) -> None:
    """AC-1: Given each preparation target, real Make requests only its
    required preparation and subsequent consumers through fake uv; setup requests
    hooks/build, package requests Python preparation then offline smoke routing,
    and ci-check prepares hooks before checks and audit.

    AC-2: Each CI target prepares what its checks require, and missing required
    environments fail clearly. `make setup` still prepares hooks and build
    tooling for subsequent offline checks.

    AC-3: Prepared offline checks remain network-free, reject a missing or
    stale environment, and exercise the installed package outside the
    worktree. Dependency synchronization stays locked and audit remains
    required by full CI.

    This case covers development setup routing/flags only. It does not cover
    actual installs, network isolation, stale environments, or installed-package
    execution.
    """
    # Given
    repository = creation_repository(tmp_path / "setup")
    sandbox = repository.sandbox
    cache_marker = sandbox.directory / ".cache/uv/ready"
    cache_marker.parent.mkdir(parents=True)
    cache_marker.write_text("cached")
    git_dir = repository.git("rev-parse", "--absolute-git-dir").stdout.strip()

    # When
    result = sandbox.run(
        "setup",
        environment={"UV_PROJECT_ENVIRONMENT": str(sandbox.directory / ".venv")},
    )

    # Then
    assert result.exit_code == 0, result.output
    assert [call.argv for call in result.calls] == [
        ("sync", "--locked", "--group", "dev"),
        (
            "run",
            "--no-sync",
            "prek",
            "install",
            "--prepare-hooks",
            "--hook-type",
            "pre-commit",
            "--hook-type",
            "commit-msg",
            "--git-dir",
            git_dir,
        ),
        ("build", "--wheel", "--out-dir", ".cache/build"),
    ]


def test_package_prepares_python_then_requests_offline_smoke(
    sandbox: MakeSandbox,
) -> None:
    """Covers online package preparation followed by offline wheel smoke routing."""
    # Given: the sandbox fixture supplies the disposable environment.

    # When
    result = sandbox.run("ci-package")

    # Then
    assert result.exit_code == 0, result.output
    assert [call.argv for call in result.calls] == [
        ("python", "install"),
        ("build", "--wheel", "--out-dir", ".cache/build"),
        ("run", "python", "script/smoke_installed_package.py"),
    ]
    assert [
        (call.environment["UV_OFFLINE"], call.environment["UV_NO_SYNC"])
        for call in result.calls
    ] == [(None, "true"), (None, "true"), ("true", "true")]


def test_package_stops_after_python_preparation_refusal(sandbox: MakeSandbox) -> None:
    """Covers AC-1: Python preparation refusal stops build and offline smoke."""
    # Given
    distinctive_error = "python preparation refused"

    # When
    result = sandbox.run(
        "ci-package",
        fail_args=("python", "install"),
        exit_code=17,
        stderr=f"{distinctive_error}\n",
    )

    # Then
    assert result.exit_code == 2
    assert distinctive_error in result.output
    assert "Error 17" in result.output
    assert [call.argv for call in result.calls] == [("python", "install")]
    assert [
        (call.environment["UV_OFFLINE"], call.environment["UV_NO_SYNC"])
        for call in result.calls
    ] == [(None, "true")]


def test_package_stops_after_backend_preparation_refusal(sandbox: MakeSandbox) -> None:
    """Covers AC-1: backend refusal prevents offline smoke and preserves Make error."""
    # Given
    build_arguments = ("build", "--wheel", "--out-dir", ".cache/build")
    distinctive_error = "backend wheel preparation refused"

    # When
    result = sandbox.run(
        "ci-package",
        fail_args=build_arguments,
        exit_code=23,
        stderr=f"{distinctive_error}\n",
    )

    # Then
    assert result.exit_code == 2
    assert distinctive_error in result.output
    assert "Error 23" in result.output
    assert [call.argv for call in result.calls] == [
        ("python", "install"),
        build_arguments,
    ]
    assert [
        (call.environment["UV_OFFLINE"], call.environment["UV_NO_SYNC"])
        for call in result.calls
    ] == [(None, "true"), (None, "true")]


def test_ci_check_prepares_dependencies_and_hooks_before_checks_and_audit(
    sandbox: MakeSandbox,
) -> None:
    """AC-1: Given each preparation target, real Make requests only its
    required preparation and subsequent consumers through fake uv; setup requests
    hooks/build, package requests Python preparation then offline smoke routing,
    and ci-check prepares hooks before checks and audit.

    AC-2: Each CI target prepares what its checks require, and missing required
    environments fail clearly. `make setup` still prepares hooks and build
    tooling for subsequent offline checks.

    AC-3: Prepared offline checks remain network-free, reject a missing or
    stale environment, and exercise the installed package outside the
    worktree. Dependency synchronization stays locked and audit remains
    required by full CI.

    This case covers CI static preparation and audit routing/flags only.
    It does not cover
    actual installs, network isolation, stale environments, or installed-package
    execution.
    """
    # Given: the sandbox fixture supplies the disposable environment.

    # When
    result = sandbox.run("ci-check")

    # Then
    assert result.exit_code == 0, result.output
    assert [call.argv for call in result.calls[:2]] == [
        ("sync", "--locked", "--group", "dev"),
        ("run", "--no-sync", "prek", "prepare-hooks"),
    ]
    assert ("run", "ruff", "check", ".") in [call.argv for call in result.calls[2:-1]]
    assert result.calls[-1].argv == ("audit", "--frozen", "--preview-features", "audit")
