# SPDX-License-Identifier: Apache-2.0
"""Exercise Markdown tool behavior and Make target wiring."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUMDL = shutil.which("rumdl")


def run_rumdl(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    if RUMDL is None:
        pytest.fail("rumdl must be installed from the development dependencies")
    return subprocess.run(
        [RUMDL, args[0], "--config", str(ROOT / "pyproject.toml"), *args[1:]],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_rumdl_formats_prose_and_tables_preserving_literals(tmp_path: Path) -> None:
    path = tmp_path / "guide.md"
    frontmatter = '---\ntitle: "Keep  these spaces"\n---\n'
    mermaid = "```mermaid\ngraph TD\n  A[Start] --> B[Finish]\n```"
    inline_code = "`literal [link](missing.md)`"
    long_prose = (
        "This sentence is deliberately long enough to wrap across multiple lines "
        "while preserving its words, punctuation, and final meaning."
    )
    link = "[target](../guide.md#heading)"
    long_url = "[external](https://example.invalid/" + "segment-" * 12 + "end)"
    path.write_text(
        frontmatter
        + "# Guide\n\n"
        + long_prose
        + "\n\n"
        + link
        + "\n\n"
        + long_url
        + "\n\n"
        + inline_code
        + "\n\n"
        + mermaid
        + "\n\n"
        + "| Key | Description |\n| --- | --- |\n| a | short |\n"
        + "| longer | a longer description |\n",
        encoding="utf-8",
    )

    formatted = run_rumdl("fmt", str(path), cwd=tmp_path)
    assert formatted.returncode == 0, formatted.stdout + formatted.stderr
    result = path.read_text(encoding="utf-8")
    assert result.startswith(frontmatter)
    assert mermaid in result
    assert link in result
    assert long_url in result
    assert inline_code in result
    assert "| Key" in result and "| longer" in result
    assert "| a      | short" in result
    wrapped_prose = result[result.index("This sentence") : result.index(link)].strip()
    wrapped_lines = wrapped_prose.splitlines()
    assert len(wrapped_lines) > 1
    assert " ".join(line.strip() for line in wrapped_lines) == long_prose

    repeated = run_rumdl("fmt", str(path), cwd=tmp_path)
    assert repeated.returncode == 0, repeated.stdout + repeated.stderr
    assert path.read_text(encoding="utf-8") == result
    checked = run_rumdl("fmt", "--check", str(path), cwd=tmp_path)
    assert checked.returncode == 0, checked.stdout + checked.stderr


def test_rumdl_format_check_does_not_modify_files(tmp_path: Path) -> None:
    path = tmp_path / "unformatted.md"
    path.write_text("# Heading\n\n" + "Long prose " * 12 + "\n", encoding="utf-8")
    before = path.read_bytes()

    checked = run_rumdl("fmt", "--check", str(path), cwd=tmp_path)

    assert checked.returncode != 0
    assert path.read_bytes() == before


def test_rumdl_checks_offline_local_links_but_not_literal_or_external_links(
    tmp_path: Path,
) -> None:
    (tmp_path / "guide.md").write_text(
        "# Guide\n\n## Repeat\n\n## Repeat\n", encoding="utf-8"
    )
    source = tmp_path / "README.md"
    source.write_text(
        "# Index\n\n[second heading](guide.md#repeat-1)\n\n"
        "[external](https://example.invalid/not-fetched)\n\n"
        "Literal `[missing](missing.md)` remains code.\n\n"
        "```mermaid\ngraph TD\nA --> |[missing](missing.md)| B\n```\n",
        encoding="utf-8",
    )

    # Duplicate headings exercise rumdl's -1 anchor behavior; suppress only
    # the independent duplicate-heading style rule in this focused probe.
    valid = run_rumdl("check", "--disable", "MD024", str(tmp_path), cwd=tmp_path)
    assert valid.returncode == 0, valid.stdout + valid.stderr

    with source.open("a", encoding="utf-8") as output:
        output.write(
            "\n[missing file](missing.md)\n[missing heading](guide.md#absent)\n"
        )
    invalid = run_rumdl("check", "--disable", "MD024", str(tmp_path), cwd=tmp_path)
    assert invalid.returncode != 0
    assert "MD057" in invalid.stdout + invalid.stderr
    assert "MD051" in invalid.stdout + invalid.stderr


def run_make(target: str, *args: str, env: dict[str, str] | None = None):
    return subprocess.run(
        ["make", target, *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


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


@pytest.mark.parametrize("mutation", ["rename", "delete"])
def test_make_doc_check_finds_inbound_links_to_changed_heading(
    tmp_path: Path, mutation: str
) -> None:
    target = tmp_path / f"target-{mutation}.md"
    source = tmp_path / f"source-{mutation}.md"
    target.write_text("# Guide\n\n## Overview\n", encoding="utf-8")
    source.write_text(f"[Overview]({target.name}#overview)\n", encoding="utf-8")
    if mutation == "rename":
        target.write_text("# Guide\n\n## Summary\n", encoding="utf-8")
    else:
        target.write_text("# Guide\n", encoding="utf-8")

    result = run_make("doc-check", f"ARGS={source} {target}")
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "MD051" in output
    assert source.name in output
    assert target.name in output


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
