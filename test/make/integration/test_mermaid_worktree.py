# SPDX-License-Identifier: Apache-2.0
"""Exercise Mermaid worktree routing and cleanup through real Make and Git."""

from pathlib import Path

import pytest

from test.make.worktree_support import files_under, mermaid_repository


@pytest.mark.parametrize(
    (
        "cache_files",
        "render_status",
        "expected_status",
        "expected_diagnostic",
        "render_runs",
    ),
    [
        (
            ((".cache/uv/ready", "cached dependencies"),),
            0,
            0,
            "Disposable worktree and branch cleaned:",
            True,
        ),
        ((), 0, 2, "Error 17", False),
        (((".cache/uv/ready", "cached dependencies"),), 23, 2, "Error 23", True),
        (((".cache/uv/ready", "cached dependencies"),), 124, 2, "Error 124", True),
    ],
    ids=["success", "preparation-failure", "render-failure", "timeout-status"],
)
@pytest.mark.covers(
    work="doc/feat/mermaid-adoption/setup/worktree/README.md", ac="AC-3"
)
def test_mermaid_route_cleans_owned_state_and_preserves_callers(
    tmp_path: Path,
    cache_files: tuple[tuple[str, str], ...],
    render_status: int,
    expected_status: int,
    expected_diagnostic: str,
    render_runs: bool,
) -> None:
    """Clean route artifacts, preserve source state, and retain child failures.

    The render double's 124 status checks timeout-status propagation; the
    subprocess helper test covers timeout signaling and reaping.
    """
    # Given
    repository = mermaid_repository(tmp_path / "repository", cache_files=cache_files)
    source = repository.sandbox.directory
    before_files = files_under(source)
    before_files.pop("uv-calls.jsonl", None)
    before_git = repository.state()

    # When
    result = repository.sandbox.run(
        "verify-mermaid-worktree",
        environment={
            "STUB_RENDER_EXIT": str(render_status),
            "STUB_UV_EXECUTE_ROUTE": "true",
        },
        timeout=30,
    )

    # Then
    assert result.exit_code == expected_status, result.output
    assert repository.state() == before_git
    after_files = files_under(source)
    after_files.pop("uv-calls.jsonl", None)
    assert after_files == before_files
    assert expected_diagnostic in result.output
    assert (
        any(
            call.argv
            == ("run", "pytest", "test/script/integration/test_mermaid_backend.py")
            for call in result.calls
        )
        is render_runs
    )
