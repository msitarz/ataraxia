# SPDX-License-Identifier: Apache-2.0
"""Exercise our Markdown Make boundary using prepared real tools and files."""

from collections.abc import Mapping
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from test.make.support import ROOT, MakeResult

VALID_MERMAID = "# Mermaid\n\n```mermaid\nflowchart LR\n    A --> B\n```\n"
INVALID_MERMAID = "# Mermaid\n\n```mermaid\nthis is not Mermaid\n```\n"


@dataclass(frozen=True)
class MarkdownSandbox:
    """Disposable Make/config files using the prepared tool environment."""

    directory: Path
    environment: dict[str, str]

    def run(
        self, *arguments: str, environment: Mapping[str, str] | None = None
    ) -> MakeResult:
        """Capture actual Make and real uv diagnostics under explicit state."""
        result = subprocess.run(
            ["make", *arguments],
            cwd=self.directory,
            env=self.environment | dict(environment or {}),
            capture_output=True,
            text=True,
            timeout=60,
        )
        return MakeResult(result.returncode, result.stdout, result.stderr, ())


@pytest.fixture
def markdown_sandbox(tmp_path: Path) -> MarkdownSandbox:
    """Copy actual Make/config while reusing only prepared external tools."""
    uv = shutil.which("uv")
    if uv is None:
        pytest.fail("real uv is required for Markdown Make boundary tests")
    directory = tmp_path / "repo"
    directory.mkdir()
    shutil.copyfile(ROOT / "Makefile", directory / "Makefile")
    shutil.copyfile(ROOT / "pyproject.toml", directory / "pyproject.toml")
    scripts = directory / "script"
    scripts.mkdir()
    shutil.copyfile(
        ROOT / "script" / "validate_mermaid.py",
        scripts / "validate_mermaid.py",
    )
    home, scratch = tmp_path / "home", tmp_path / "tmp"
    home.mkdir()
    scratch.mkdir()
    return MarkdownSandbox(
        directory,
        {
            "PATH": os.pathsep.join((str(Path(uv).parent), "/usr/bin", "/bin")),
            "HOME": str(home),
            "TMPDIR": str(scratch),
            "UV_PROJECT_ENVIRONMENT": str(ROOT / ".venv"),
            "UV_CACHE_DIR": str(ROOT / ".cache/uv"),
            "UV_PYTHON": sys.executable,
            "UV_OFFLINE": "true",
            "UV_NO_SYNC": "true",
        },
    )


@pytest.mark.real_tool
def test_make_doc_check_rejects_formatting_without_modifying_files(
    markdown_sandbox: MarkdownSandbox,
) -> None:
    """Stop before Mermaid validation when Markdown formatting fails."""
    # Given
    path = markdown_sandbox.directory / "unformatted.md"
    path.write_text("# Heading\n\n" + "Long prose " * 12 + "\n\n" + INVALID_MERMAID)
    before = path.read_bytes()

    # When
    result = markdown_sandbox.run("doc-check", f"ARGS={path}")

    # Then
    assert result.exit_code == 2, result.output
    assert "MD013" in result.output
    assert "UnknownDiagramError" not in result.output
    assert path.name in result.output
    assert path.read_bytes() == before


@pytest.mark.real_tool
def test_make_doc_format_selects_files_and_directories_and_excludes_artifacts(
    markdown_sandbox: MarkdownSandbox,
) -> None:
    """Format selected Markdown without validating Mermaid fences."""
    # Given
    directory = markdown_sandbox.directory
    selected_dir = directory / "selected-dir"
    nested = selected_dir / "nested"
    nested.mkdir(parents=True)
    first, second = selected_dir / "first.md", nested / "second.md"
    selected_file, unselected = (
        directory / "selected-file.md",
        directory / "unselected.md",
    )
    excluded = selected_dir / ".cache/generated.md"
    malformed_diagram = selected_dir / "malformed-diagram.md"
    excluded.parent.mkdir()
    source = "# Heading\n\n" + "Long prose " * 12 + "\n"
    first.write_text(source)
    second.write_text(source)
    selected_file.write_text(source)
    unselected.write_text(source)
    excluded.write_text(source)
    malformed_diagram.write_text(INVALID_MERMAID)
    untouched = {
        path: path.read_bytes() for path in (unselected, excluded, malformed_diagram)
    }

    # When
    result = markdown_sandbox.run("doc-format", f"ARGS={selected_dir} {selected_file}")

    # Then
    assert result.exit_code == 0, result.output
    formatted = tuple(path.read_text() for path in (first, second, selected_file))
    assert all(text != source for text in formatted)
    assert all(text.split() == source.split() for text in formatted)
    assert all(max(map(len, text.splitlines())) <= 80 for text in formatted)
    assert {path: path.read_bytes() for path in untouched} == untouched


@pytest.mark.real_tool
def test_make_doc_format_reflows_external_file_with_repository_config(
    markdown_sandbox: MarkdownSandbox, tmp_path: Path
) -> None:
    """AC-1: Given valid, malformed, or missing-tool documentation
    arrangements, Make changes only selected files or fails visibly with required
    files unchanged.

    This case covers repository-config formatting outside the copied checkout.
    """
    # Given
    path = tmp_path / "pr-description.md"
    source = "# Description\n\n" + "Long prose " * 12 + "\n"
    path.write_text(source)

    # When
    result = markdown_sandbox.run("doc-format", f"ARGS={path}")

    # Then
    assert result.exit_code == 0, result.output
    formatted = path.read_text()
    assert formatted != source
    assert max(map(len, formatted.splitlines())) <= 80
    assert formatted.split() == source.split()


@pytest.mark.parametrize(
    "changed", ["# Guide\n\n## Summary\n", "# Guide\n"], ids=["rename", "delete"]
)
@pytest.mark.real_tool
def test_make_doc_check_finds_inbound_links_to_changed_heading(
    markdown_sandbox: MarkdownSandbox, changed: str
) -> None:
    """Find inbound links from unselected docs when a target heading changes."""
    # Given
    target, source = (
        markdown_sandbox.directory / name for name in ("target.md", "source.md")
    )
    target.write_text(changed)
    source.write_text("[Overview](target.md#overview)\n")
    before = {path: path.read_bytes() for path in (target, source)}

    # When: only the changed target is selected, requiring a full graph scan.
    result = markdown_sandbox.run("doc-check", f"ARGS={target}")

    # Then
    assert result.exit_code == 2, result.output
    assert "MD051" in result.output
    assert source.name in result.output
    assert target.name in result.output
    assert {path: path.read_bytes() for path in before} == before


@pytest.mark.real_tool
def test_make_doc_check_fails_visibly_when_rumdl_is_missing(
    markdown_sandbox: MarkdownSandbox, tmp_path: Path
) -> None:
    """AC-1: Given valid, malformed, or missing-tool documentation
    arrangements, Make changes only selected files or fails visibly with required
    files unchanged.

    This case covers missing-tool refusal without installation or document mutation.
    """
    # Given
    path = markdown_sandbox.directory / "guide.md"
    path.write_text("# Guide\n")
    before = path.read_bytes()
    environment = {
        "UV_PROJECT_ENVIRONMENT": str(tmp_path / "empty-venv"),
        "UV_CACHE_DIR": str(tmp_path / "uv-cache"),
    }

    # When
    result = markdown_sandbox.run("doc-check", environment=environment)

    # Then
    assert result.exit_code == 2, result.output
    assert "rumdl" in result.output.lower()
    assert "Failed to spawn" in result.stderr
    assert "No such file or directory" in result.stderr
    assert "install" not in result.output.lower()
    assert path.read_bytes() == before


@pytest.mark.real_tool
def test_doc_check_validates_only_selected_nested_mermaid_files(
    markdown_sandbox: MarkdownSandbox,
) -> None:
    """Validate nested selected Mermaid while ignoring invalid unselected source."""
    # Given
    docs = markdown_sandbox.directory / "docs"
    selected = docs / "selected" / "nested"
    selected.mkdir(parents=True)
    selected_file = selected / "guide.md"
    unselected_file = docs / "unselected.md"
    selected_file.write_text(VALID_MERMAID)
    unselected_file.write_text(INVALID_MERMAID)
    before = {path: path.read_bytes() for path in (selected_file, unselected_file)}

    # When
    result = markdown_sandbox.run("doc-check", f"ARGS={selected}")

    # Then
    assert result.exit_code == 0, result.output
    assert "UnknownDiagramError" not in result.output
    assert "<svg" not in result.output
    assert {path: path.read_bytes() for path in before} == before
    assert list(markdown_sandbox.directory.rglob("*.svg")) == []


@pytest.mark.real_tool
def test_doc_check_reports_actual_mermaid_backend_failure(
    markdown_sandbox: MarkdownSandbox,
) -> None:
    """Show backend diagnostics for malformed Mermaid in a selected file."""
    # Given
    path = markdown_sandbox.directory / "nested" / "invalid.md"
    path.parent.mkdir()
    path.write_text(INVALID_MERMAID)
    before = path.read_bytes()

    # When
    result = markdown_sandbox.run("doc-check", f"ARGS={path}")

    # Then
    assert result.exit_code == 2, result.output
    assert path.name in result.output
    assert f"{path.name}:3:" in result.output
    assert "UnknownDiagramError" in result.output
    assert path.read_bytes() == before
    assert list(markdown_sandbox.directory.rglob("*.svg")) == []


@pytest.mark.real_tool
def test_doc_check_fails_when_validator_binary_is_missing(
    markdown_sandbox: MarkdownSandbox,
) -> None:
    """Fail visibly when rumdl cannot find the configured validator executable."""
    # Given
    path = markdown_sandbox.directory / "guide.md"
    path.write_text(VALID_MERMAID)
    config_path = markdown_sandbox.directory / "pyproject.toml"
    config = config_path.read_text(encoding="utf-8")
    command = 'command = ["python", "script/validate_mermaid.py"]'
    config_path.write_text(
        config.replace(command, 'command = ["missing-mermaid-validator"]'),
        encoding="utf-8",
    )

    # When
    result = markdown_sandbox.run("doc-check", f"ARGS={path}")

    # Then
    assert result.exit_code == 2, result.output
    assert "missing-mermaid-validator" in result.output
    assert "missing" in result.output.lower()


@pytest.mark.real_tool
@pytest.mark.parametrize(
    ("source", "expected_exit", "has_backend_error"),
    [
        pytest.param(VALID_MERMAID, 0, False, id="valid-default-selection"),
        pytest.param(INVALID_MERMAID, 2, True, id="invalid-default-selection"),
        pytest.param("# No diagrams\n", 0, False, id="no-diagram-default-selection"),
    ],
)
def test_doc_check_defaults_to_all_files_and_respects_exclusions(
    markdown_sandbox: MarkdownSandbox,
    source: str,
    expected_exit: int,
    has_backend_error: bool,
) -> None:
    """Validate default-scope Mermaid while respecting configured exclusions."""
    # Given
    directory = markdown_sandbox.directory
    guide = directory / "guide.md"
    excluded = directory / ".cache" / "ignored.md"
    excluded.parent.mkdir()
    guide.write_text(source)
    excluded.write_text(INVALID_MERMAID)
    before = {path: path.read_bytes() for path in (guide, excluded)}

    # When
    result = markdown_sandbox.run("doc-check")

    # Then
    assert result.exit_code == expected_exit, result.output
    assert ("UnknownDiagramError" in result.output) is has_backend_error
    assert "<svg" not in result.output
    assert excluded.name not in result.output
    assert {path: path.read_bytes() for path in before} == before
    assert list(directory.rglob("*.svg")) == []


def test_make_help_lists_markdown_targets(markdown_sandbox: MarkdownSandbox) -> None:
    """List existing Markdown targets and the scoped Mermaid target."""
    # Given: the fixture supplies the actual Makefile in a disposable directory.

    # When
    result = markdown_sandbox.run("help")

    # Then
    assert result.exit_code == 0, result.output
    assert "make doc-check" in result.stdout
    assert "make doc-check-mermaid" in result.stdout
    assert "make doc-format" in result.stdout
