# SPDX-License-Identifier: Apache-2.0
"""Check ordinary command forwarding through real Make and recording uv."""

from pathlib import Path

import pytest

from test.make.support import MakeSandbox, make_sandbox


@pytest.fixture
def sandbox(tmp_path: Path) -> MakeSandbox:
    """Provide a fresh disposable Makefile and isolated child environment."""
    return make_sandbox(tmp_path)


@pytest.mark.parametrize(
    ("target", "args", "expected"),
    [
        (
            "lint",
            (),
            [["run", "ruff", "check", ".", "--fix"]],
        ),
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
                    "test/script/typecheck/markdown_contracts.py",
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
    ids=[
        "lint-default",
        "lint-selected",
        "lint-check-selected",
        "format-default",
        "format-selected",
        "format-check-selected",
        "test-default",
        "test-selected",
        "typecheck-default",
        "typecheck-selected",
        "expectations-selected",
    ],
)
def test_make_tool_targets_preserve_defaults_and_route_selectors(
    sandbox: MakeSandbox, target: str, args: tuple[str, ...], expected: list[list[str]]
) -> None:
    """Route default and selected paths to ordinary Make tool targets."""
    # Given: the sandbox fixture supplies an isolated real-Make arrangement.

    # When
    result = sandbox.run(target, *args)

    # Then
    assert result.exit_code == 0, result.output
    assert [list(call.argv) for call in result.calls] == expected


def test_lint_check_propagates_ruff_failure(sandbox: MakeSandbox) -> None:
    """The single Ruff check failure propagates from Make."""
    # Given: the sandbox fixture supplies an isolated real-Make arrangement.

    # When
    result = sandbox.run(
        "lint-check", fail_args=("run", "ruff", "check", "."), exit_code=2
    )

    # Then
    assert result.exit_code == 2
    assert len(result.calls) == 1
    assert result.calls[0].argv == ("run", "ruff", "check", ".")


def test_markdown_targets_preserve_graph_and_selected_mermaid_scope(
    sandbox: MakeSandbox,
) -> None:
    """Route Markdown link checks over the graph and Mermaid over selected paths."""
    # Given: the sandbox fixture supplies an isolated real-Make arrangement.

    # When
    result = sandbox.run("doc-check", "ARGS=doc/acceptance-tracing.md")

    # Then
    assert result.exit_code == 0, result.output
    assert [list(call.argv) for call in result.calls] == [
        [
            "run",
            "rumdl",
            "check",
            "--no-code-block-tools",
            "doc/acceptance-tracing.md",
            ".",
        ],
        [
            "run",
            "rumdl",
            "fmt",
            "--check",
            "--no-code-block-tools",
            "doc/acceptance-tracing.md",
        ],
        [
            "run",
            "rumdl",
            "check",
            "--only-code-block-tools",
            "--no-cache",
            "doc/acceptance-tracing.md",
        ],
        ["run", "python", "-m", "script.work_check"],
    ]


def test_markdown_format_target_passes_selected_paths(sandbox: MakeSandbox) -> None:
    """AC-1: Given ordinary targets and hostile arguments, recorded commands
    match promised routing, invalid inputs fail before tool invocation, and shell
    expressions never create marker files.

    This case covers the named command forwarding obligation.
    """
    # Given: the sandbox fixture supplies an isolated real-Make arrangement.

    # When
    result = sandbox.run("doc-format", "ARGS=doc/acceptance-tracing.md")

    # Then
    assert result.exit_code == 0, result.output
    assert [list(call.argv) for call in result.calls] == [
        [
            "run",
            "rumdl",
            "fmt",
            "--no-code-block-tools",
            "--config",
            "pyproject.toml",
            "doc/acceptance-tracing.md",
        ]
    ]


def test_make_selectors_quote_shell_metacharacters(sandbox: MakeSandbox) -> None:
    """AC-1: Given ordinary targets and hostile arguments, recorded commands
    match promised routing, invalid inputs fail before tool invocation, and shell
    expressions never create marker files.

    This case covers literal selector transport and absent execution markers.
    """
    # Given: the sandbox fixture supplies an isolated real-Make arrangement.

    marker = sandbox.directory / "should-not-be-created"
    selector = f"src/example.py; touch {marker}"

    # When
    result = sandbox.run("lint-check", f"ARGS={selector}")

    # Then
    assert result.exit_code == 0, result.output
    assert [list(call.argv) for call in result.calls] == [
        ["run", "ruff", "check", "src/example.py;", "touch", str(marker)]
    ]
    assert not marker.exists()


def test_make_selectors_quote_single_quotes(sandbox: MakeSandbox) -> None:
    """AC-1: Given ordinary targets and hostile arguments, recorded commands
    match promised routing, invalid inputs fail before tool invocation, and shell
    expressions never create marker files.

    This case covers the named command forwarding obligation.
    """
    # Given: the sandbox fixture supplies an isolated real-Make arrangement.

    # When
    result = sandbox.run("format-check", "ARGS=src/example's.py")

    # Then
    assert result.exit_code == 0, result.output
    assert [list(call.argv) for call in result.calls] == [
        ["run", "ruff", "format", "--check", "src/example's.py"]
    ]


def test_path_selectors_reject_tool_options(sandbox: MakeSandbox) -> None:
    """AC-1: Given ordinary targets and hostile arguments, recorded commands
    match promised routing, invalid inputs fail before tool invocation, and shell
    expressions never create marker files.

    This case covers option refusal before uv invocation.
    """
    # Given: the sandbox fixture supplies an isolated real-Make arrangement.

    # When
    result = sandbox.run("lint-check", "ARGS=--fix")

    # Then
    assert result.exit_code == 2
    assert "ARGS accepts paths, not options" in result.stderr
    assert [list(call.argv) for call in result.calls] == []


def test_run_target_routes_project_cli_arguments(sandbox: MakeSandbox) -> None:
    """AC-1: Given ordinary targets and hostile arguments, recorded commands
    match promised routing, invalid inputs fail before tool invocation, and shell
    expressions never create marker files.

    This case covers the named command forwarding obligation.
    """
    # Given: the sandbox fixture supplies an isolated real-Make arrangement.

    # When
    result = sandbox.run(
        "run",
        "CLI_ARGS=--sink example/crossover.py "
        "--shards-dir sample --output results.json",
    )

    # Then
    assert result.exit_code == 0, result.output
    assert [list(call.argv) for call in result.calls] == [
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


def test_run_target_requires_cli_arguments(sandbox: MakeSandbox) -> None:
    """AC-1: Given ordinary targets and hostile arguments, recorded commands
    match promised routing, invalid inputs fail before tool invocation, and shell
    expressions never create marker files.

    This case covers missing CLI argument refusal before uv invocation.
    """
    # Given: the sandbox fixture supplies an isolated real-Make arrangement.

    # When
    result = sandbox.run("run")

    # Then
    assert result.exit_code == 2
    assert "CLI_ARGS" in result.stderr
    assert [list(call.argv) for call in result.calls] == []


def test_cli_arguments_quote_shell_metacharacters(sandbox: MakeSandbox) -> None:
    """AC-1: Given ordinary targets and hostile arguments, recorded commands
    match promised routing, invalid inputs fail before tool invocation, and shell
    expressions never create marker files.

    This case covers literal CLI transport and absent execution markers.
    """
    # Given: the sandbox fixture supplies an isolated real-Make arrangement.

    marker = sandbox.directory / "should-not-be-created"
    cli_args = f"--option value; touch {marker}"

    # When
    result = sandbox.run("run", f"CLI_ARGS={cli_args}")

    # Then
    assert result.exit_code == 0, result.output
    assert [list(call.argv) for call in result.calls] == [
        ["run", "ataraxia", "--option", "value;", "touch", str(marker)]
    ]
    assert not marker.exists()


def test_dependency_lock_target_uses_uv_lock(sandbox: MakeSandbox) -> None:
    """AC-1: Given ordinary targets and hostile arguments, recorded commands
    match promised routing, invalid inputs fail before tool invocation, and shell
    expressions never create marker files.

    This case covers the named command forwarding obligation.
    """
    # Given: the sandbox fixture supplies an isolated real-Make arrangement.

    # When
    result = sandbox.run("deps-lock")

    # Then
    assert result.exit_code == 0, result.output
    assert [list(call.argv) for call in result.calls] == [["lock"]]
