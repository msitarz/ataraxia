# SPDX-License-Identifier: Apache-2.0
"""Exercise Markdown tool behavior and Make target wiring."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

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
    assert "\n" in result[result.index("This sentence") : result.index(inline_code)]

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


def test_make_markdown_targets_are_offline_and_respect_selection(
    tmp_path: Path,
) -> None:
    log = tmp_path / "calls.jsonl"
    uv = tmp_path / "uv"
    uv.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "with open(os.environ['DOC_TOOLS_LOG'], 'a') as log:\n"
        "    log.write(json.dumps([sys.argv[1:], os.getenv('UV_OFFLINE'), "
        "os.getenv('UV_NO_SYNC')]) + '\\n')\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    selected = tmp_path / "selected.md"
    selected.write_text("# Selected\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(PATH=f"{tmp_path}:{env['PATH']}", DOC_TOOLS_LOG=str(log))
    env.pop("UV_OFFLINE", None)
    env.pop("UV_NO_SYNC", None)

    result = subprocess.run(
        ["make", "doc-check", f"ARGS={selected}"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert [call[0] for call in calls] == [
        ["run", "rumdl", "check", str(selected), "."],
        ["run", "rumdl", "fmt", "--check", str(selected)],
    ]
    assert all(offline == no_sync == "true" for _, offline, no_sync in calls)

    log.write_text("", encoding="utf-8")
    formatted = subprocess.run(
        ["make", "doc-format", f"ARGS={selected}"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert formatted.returncode == 0, formatted.stdout + formatted.stderr
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert [call[0] for call in calls] == [["run", "rumdl", "fmt", str(selected)]]
    assert all(offline == no_sync == "true" for _, offline, no_sync in calls)

    log.write_text("", encoding="utf-8")
    format_all = subprocess.run(
        ["make", "doc-format"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert format_all.returncode == 0, format_all.stdout + format_all.stderr
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert [call[0] for call in calls] == [["run", "rumdl", "fmt", "."]]

    help_result = subprocess.run(
        ["make", "help"], cwd=ROOT, capture_output=True, text=True, timeout=30
    )
    assert help_result.returncode == 0, help_result.stdout + help_result.stderr
    assert "make doc-check" in help_result.stdout
    assert "make doc-format" in help_result.stdout
