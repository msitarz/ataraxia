# SPDX-License-Identifier: Apache-2.0
"""Smoke-test the prepared QuickJS renderer used by offline setup."""

from pathlib import Path
import subprocess

import pytest


@pytest.mark.covers(work="doc/feat/mermaid-adoption/setup/README.md", ac="AC-1")
@pytest.mark.covers(work="doc/feat/mermaid-adoption/setup/README.md", ac="AC-2")
def test_prepared_quickjs_backend_renders_svg(tmp_path: Path) -> None:
    """Check forced QuickJS SVG rendering after setup or offline preparation."""
    # Given
    source = tmp_path / "diagram.mmd"
    output = tmp_path / "diagram.svg"
    source_bytes = b"flowchart LR\n    A[Start] --> B[Finish]\n"
    source.write_bytes(source_bytes)

    # When
    render = subprocess.run(
        (
            "mermaidx",
            "--backend",
            "quickjs",
            "-i",
            source.name,
            "-o",
            output.name,
        ),
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Then
    assert render.returncode == 0, render.stderr
    assert output.read_text(encoding="utf-8").startswith("<svg")
    assert source.read_bytes() == source_bytes
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "diagram.mmd",
        "diagram.svg",
    ]
