# SPDX-License-Identifier: Apache-2.0
"""User-visible success behavior of the shipped CLI."""

import json
from pathlib import Path

import pytest

from test.ataraxia.cli_process import run_cli
from test.ataraxia.cli_sample_expected import (
    load_sample_expected,
    normalize_sample_paths_and_order,
)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/cli/success/README.md",
    ac="AC-1",
)
def test_crossover_sample_cli_run(tmp_path: Path) -> None:
    """Checks the exact sample report, full artifact, output and unchanged inputs."""
    # Given
    project = Path(__file__).resolve().parents[3]
    strategy = project / "example/crossover.py"
    shards = (
        project / "sample/nq_15m_2026_07_19.csv",
        project / "sample/nq_15m_2026_07_20.csv",
    )
    inputs = (strategy, *shards)
    input_bytes = tuple(path.read_bytes() for path in inputs)
    output = tmp_path / "output.json"

    # When
    result = run_cli(
        ["-s", strategy, "-d", project / "sample", "-o", output],
        cwd=tmp_path,
        project=project,
        state=tmp_path / "process-state",
    )

    # Then
    assert result.exit_code == 0
    assert result.stdout == (
        "Aggregated backtest results:\nRealized PnL   = 40\nUnrealized PnL = 0\n"
    )
    assert result.stderr == ""
    assert output.is_file()
    actual: object = json.loads(output.read_text(encoding="utf-8"))
    assert normalize_sample_paths_and_order(actual, project) == load_sample_expected()
    assert tuple(path.read_bytes() for path in inputs) == input_bytes
