# SPDX-License-Identifier: Apache-2.0
"""Check offline execution and full-scope obligations through real Make."""

from pathlib import Path

import pytest

from test.make.support import MakeSandbox, make_sandbox


@pytest.fixture
def sandbox(tmp_path: Path) -> MakeSandbox:
    """Provide an isolated real-Make environment and recording uv."""
    return make_sandbox(tmp_path)


REQUIRED_CONSUMERS = {
    ("run", "ruff", "check", "."),
    ("run", "tach", "check"),
    ("run", "pytest", "--cov"),
    ("run", "pytest", "example/"),
    ("run", "python", "script/smoke_installed_package.py"),
}


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/check-orchestration/execution/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/ci-preparation/README.md",
    ac="AC-3",
)
def test_verify_runs_required_consumers_offline_without_preparation_or_audit(
    sandbox: MakeSandbox,
) -> None:
    """AC-1: Given verify/CI execution, required local checks receive offline
    and no-sync flags; verify omits preparation/audit, CI preserves required order
    and audit environment, and injected setup/audit failures return Make code 2
    with required later commands absent.

    AC-3: Prepared offline checks remain network-free, reject a missing or
    stale environment, and exercise the installed package outside the
    worktree. Dependency synchronization stays locked and audit remains
    required by full CI.

    This case covers verify execution routing/flags only; the recorder does not
    prove actual network isolation, environment freshness, or package execution.
    """
    # Given: the sandbox fixture supplies a prepared-command recorder.

    # When
    result = sandbox.run("verify")

    # Then
    assert result.exit_code == 0, result.output
    assert {call.argv for call in result.calls} >= REQUIRED_CONSUMERS
    assert {
        (call.environment["UV_OFFLINE"], call.environment["UV_NO_SYNC"])
        for call in result.calls
    } == {("true", "true")}
    assert not any(
        call.argv[0] == "audit" or "prepare-hooks" in call.argv for call in result.calls
    )


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/check-orchestration/execution/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/ci-preparation/README.md",
    ac="AC-3",
)
def test_verify_stops_after_the_prepared_environment_check_fails(
    sandbox: MakeSandbox,
) -> None:
    """AC-1: Given verify/CI execution, required local checks receive offline
    and no-sync flags; verify omits preparation/audit, CI preserves required order
    and audit environment, and injected setup/audit failures return Make code 2
    with required later commands absent.

    AC-3: Prepared offline checks remain network-free, reject a missing or
    stale environment, and exercise the installed package outside the
    worktree. Dependency synchronization stays locked and audit remains
    required by full CI.

    This case covers prepared-check failure routing/flags only; the recorder does not
    prove actual network isolation, environment freshness, or package execution.
    """
    # Given
    failed = ("sync", "--locked", "--group", "dev", "--check", "--offline")

    # When
    result = sandbox.run("verify", fail_args=failed)

    # Then
    assert result.exit_code == 2, result.output
    assert tuple(call.argv for call in result.calls) == (failed,)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/check-orchestration/execution/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/ci-preparation/README.md",
    ac="AC-3",
)
def test_ci_runs_local_checks_before_propagating_audit_failure(
    sandbox: MakeSandbox,
) -> None:
    """AC-1: Given verify/CI execution, required local checks receive offline
    and no-sync flags; verify omits preparation/audit, CI preserves required order
    and audit environment, and injected setup/audit failures return Make code 2
    with required later commands absent.

    AC-3: Prepared offline checks remain network-free, reject a missing or
    stale environment, and exercise the installed package outside the
    worktree. Dependency synchronization stays locked and audit remains
    required by full CI.

    This case covers CI ordering and audit failure routing/flags only.
    The recorder does not
    prove actual network isolation, environment freshness, or package execution.
    """
    # Given
    audit = ("audit", "--frozen", "--preview-features", "audit")

    # When
    result = sandbox.run("ci", fail_args=audit)

    # Then
    assert result.exit_code == 2, result.output
    assert tuple(call.argv for call in result.calls[:2]) == (
        ("sync", "--locked", "--group", "dev"),
        ("run", "--no-sync", "prek", "prepare-hooks"),
    )
    assert {call.argv for call in result.calls[2:-1]} >= REQUIRED_CONSUMERS
    assert {
        (call.environment["UV_OFFLINE"], call.environment["UV_NO_SYNC"])
        for call in result.calls[2:-1]
    } == {("true", "true")}
    assert result.calls[-1].argv == audit
    assert result.calls[-1].environment["UV_OFFLINE"] is None
    assert "Error 1" in result.stderr


@pytest.mark.parametrize("target", ["verify-check", "ci-check"], ids=["local", "ci"])
@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/check-orchestration/execution/README.md",
    ac="AC-2",
)
def test_static_checks_request_equivalent_read_only_documentation_commands(
    sandbox: MakeSandbox,
    target: str,
) -> None:
    """AC-2: Given local/CI static checks and full test/static/example
    targets with caller selectors, documentation commands remain read-only and
    equivalent, and full targets retain full scope rather than caller paths.

    This case covers documentation command/flag parity.
    """
    # Given: the sandbox fixture supplies the isolated static-check environment.

    # When
    result = sandbox.run(target)

    # Then
    assert result.exit_code == 0, result.output
    docs = tuple(call for call in result.calls if call.argv[:2] == ("run", "rumdl"))
    assert tuple(call.argv for call in docs) == (
        ("run", "rumdl", "check", "."),
        ("run", "rumdl", "fmt", "--check", "."),
    )
    assert {
        (call.environment["UV_OFFLINE"], call.environment["UV_NO_SYNC"])
        for call in docs
    } == {("true", "true")}
    assert not any(
        call.argv[:3] == ("run", "rumdl", "fmt") and "--check" not in call.argv
        for call in result.calls
    )


@pytest.mark.parametrize(
    ("target", "selector", "expected"),
    [
        ("verify-test", "test/ataraxia/unit/test_cli.py", ("run", "pytest", "--cov")),
        ("verify-examples", "example/crossover.py", ("run", "pytest", "example/")),
    ],
    ids=["full-tests", "full-examples"],
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/check-orchestration/execution/README.md",
    ac="AC-2",
)
def test_full_test_targets_ignore_caller_selectors(
    sandbox: MakeSandbox,
    target: str,
    selector: str,
    expected: tuple[str, ...],
) -> None:
    """AC-2: Given local/CI static checks and full test/static/example
    targets with caller selectors, documentation commands remain read-only and
    equivalent, and full targets retain full scope rather than caller paths.

    This case covers full test/example scope.
    """
    # Given: the parametrized selector is narrower than the promised full scope.

    # When
    result = sandbox.run(target, f"ARGS={selector}")

    # Then
    assert result.exit_code == 0, result.output
    assert tuple(call.argv for call in result.calls) == (expected,)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/check-orchestration/execution/README.md",
    ac="AC-2",
)
def test_full_static_checks_ignore_caller_paths(sandbox: MakeSandbox) -> None:
    """AC-2: Given local/CI static checks and full test/static/example
    targets with caller selectors, documentation commands remain read-only and
    equivalent, and full targets retain full scope rather than caller paths.

    This case covers full static-check scope.
    """
    # Given
    selector = "src/ataraxia/feature.py"

    # When
    result = sandbox.run("verify-check", f"ARGS={selector}")

    # Then
    assert result.exit_code == 0, result.output
    assert {
        ("run", "ruff", "check", "."),
        ("run", "ruff", "format", "--check", "."),
        ("run", "rumdl", "check", "."),
        ("run", "rumdl", "fmt", "--check", "."),
        ("run", "pyrefly", "check"),
    } <= {call.argv for call in result.calls}
    assert not any(selector in call.argv for call in result.calls)
