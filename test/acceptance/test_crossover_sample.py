# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from pathlib import Path
import subprocess


def test_crossover_sample_cli_run(tmp_path: Path):
    """Should execute example strategy with sample data via CLI."""

    output = tmp_path / "output.json"

    result = subprocess.run(
        [
            "uv",
            "run",
            "ataraxia",
            "-s",
            "example/crossover.py",
            "-d",
            "sample",
            "-o",
            output.resolve(),
        ],
        capture_output=True,
        text=True,
    )

    assert result.stderr == ""
    assert result.stdout == (
        "Aggregated backtest results:\nRealized PnL   = 40\nUnrealized PnL = 0\n"
    )

    assert len(output.read_text()) > 0
