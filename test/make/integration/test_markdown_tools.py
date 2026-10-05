# SPDX-License-Identifier: Apache-2.0
"""Exercise Markdown tool behavior and Make target wiring."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.real_tool
def test_make_doc_check_rejects_formatting_without_modifying_files() -> None:
    with tempfile.TemporaryDirectory(
        prefix=".doc-format-failure-", dir=ROOT
    ) as fixture:
        path = Path(fixture) / "unformatted.md"
        content = "# Heading\n\n" + "Long prose " * 12 + "\n"
        path.write_text(content, encoding="utf-8")
        before = path.read_bytes()

        result = run_make("doc-check", f"ARGS={path}")
        output = result.stdout + result.stderr

        assert result.returncode != 0
        assert "MD013" in output
        assert path.name in output
        assert path.read_bytes() == before


def run_make(target: str, *args: str, env: dict[str, str] | None = None):
    return subprocess.run(
        ["make", target, *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.mark.real_tool
def test_make_doc_format_selects_files_and_directories_and_excludes_artifacts() -> None:
    with tempfile.TemporaryDirectory(prefix=".doc-tools-", dir=ROOT) as fixture:
        fixture_dir = Path(fixture)
        selected_dir = fixture_dir / "selected-dir"
        nested = selected_dir / "nested"
        nested.mkdir(parents=True)
        selected_file = fixture_dir / "selected-file.md"
        unselected = fixture_dir / "unselected.md"
        excluded = selected_dir / ".cache" / "generated.md"
        excluded.parent.mkdir()
        source = "# Heading\n\n" + "Long prose " * 12 + "\n"
        for path in (
            selected_dir / "first.md",
            nested / "second.md",
            selected_file,
            unselected,
            excluded,
        ):
            path.write_text(source, encoding="utf-8")
        unselected_before = unselected.read_bytes()
        excluded_before = excluded.read_bytes()

        result = run_make("doc-format", f"ARGS={selected_dir} {selected_file}")

        assert result.returncode == 0, result.stdout + result.stderr
        for path in (selected_dir / "first.md", nested / "second.md", selected_file):
            assert path.read_text(encoding="utf-8") != source
        assert unselected.read_bytes() == unselected_before
        assert excluded.read_bytes() == excluded_before


@pytest.mark.real_tool
def test_make_doc_format_reflows_external_file_with_repository_config(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pr-description.md"
    source = "# Description\n\n" + "Long prose " * 12 + "\n"
    path.write_text(source, encoding="utf-8")

    result = run_make("doc-format", f"ARGS={path}")

    assert result.returncode == 0, result.stdout + result.stderr
    formatted = path.read_text(encoding="utf-8")
    assert formatted != source
    assert max(map(len, formatted.splitlines())) <= 80
    assert formatted.split() == source.split()


@pytest.mark.parametrize("mutation", ["rename", "delete"])
@pytest.mark.real_tool
def test_make_doc_check_finds_inbound_links_to_changed_heading(
    mutation: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix=".doc-links-", dir=ROOT) as fixture:
        fixture_dir = Path(fixture)
        target = fixture_dir / f"target-{mutation}.md"
        source = fixture_dir / f"source-{mutation}.md"
        target.write_text("# Guide\n\n## Overview\n", encoding="utf-8")
        source.write_text(f"[Overview]({target.name}#overview)\n", encoding="utf-8")
        if mutation == "rename":
            target.write_text("# Guide\n\n## Summary\n", encoding="utf-8")
        else:
            target.write_text("# Guide\n", encoding="utf-8")

        # ARGS selects only the changed target; the source is discovered by
        # doc-check's full-graph scan through the repository-root path.
        result = run_make("doc-check", f"ARGS={target}")
        output = result.stdout + result.stderr

        assert result.returncode != 0
        assert "MD051" in output
        assert source.name in output
        assert target.name in output


@pytest.mark.real_tool
def test_make_doc_check_fails_visibly_when_rumdl_is_missing(tmp_path: Path) -> None:
    tool_dirs = {
        str(Path(path).parent)
        for name in ("make", "uv")
        if (path := shutil.which(name))
    }
    tool_dirs.update({"/usr/bin", "/bin", "/usr/sbin", "/sbin"})
    env = os.environ.copy()
    env.update(
        PATH=os.pathsep.join(sorted(tool_dirs)),
        UV_PROJECT_ENVIRONMENT=str(tmp_path / "empty-venv"),
        UV_CACHE_DIR=str(tmp_path / "uv-cache"),
        UV_OFFLINE="true",
        UV_NO_SYNC="true",
    )
    env.pop("VIRTUAL_ENV", None)

    result = run_make("doc-check", env=env)
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "rumdl" in output.lower()
    assert "install" not in output.lower()


def test_make_help_lists_markdown_targets() -> None:
    result = run_make("help")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "make doc-check" in result.stdout
    assert "make doc-format" in result.stdout
