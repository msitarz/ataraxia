# SPDX-License-Identifier: Apache-2.0
"""Public CLI reporting tests using retained independent inputs."""

from copy import deepcopy
import json
from pathlib import Path

import pytest
from pytest import CaptureFixture

from ataraxia.cli import display_results, save_results
from test.ataraxia.cli_result_inputs import (
    broker_returns as arrange_broker_returns,
)
from test.ataraxia.cli_result_inputs import (
    load_reporting_expected,
)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/cli/reporting/README.md",
    ac="AC-1",
)
def test_display_results(
    capsys: CaptureFixture[str],
) -> None:
    """Reports the retained aggregate totals without writing to stderr."""
    # Given
    results = arrange_broker_returns()
    original = deepcopy(results)

    # When
    display_results(results)

    # Then
    captured = capsys.readouterr()
    assert captured.out == (
        "Aggregated backtest results:\nRealized PnL   = 80\nUnrealized PnL = -40\n"
    )
    assert captured.err == ""
    assert results == original


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/cli/reporting/README.md",
    ac="AC-1",
)
def test_save_results(tmp_path: Path) -> None:
    """Writes all retained position fields to the named output file."""
    # Given
    results = arrange_broker_returns()
    original = deepcopy(results)
    output = tmp_path / "out.json"

    # When
    save_results(results, output)

    # Then
    actual: object = json.loads(output.read_text(encoding="utf-8"))
    expected = load_reporting_expected()
    assert output.is_file()
    assert actual == expected
    assert results == original
