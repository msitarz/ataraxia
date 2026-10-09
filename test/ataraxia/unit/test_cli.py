# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from pathlib import Path
from unittest.mock import patch

from _pytest.capture import CaptureFixture
import pytest

from ataraxia.cli import main


def test_main_print_error_and_exit(capsys: CaptureFixture):
    """Should print error and exit with code 1 if no broker results."""
    with (
        patch(
            "ataraxia.cli.sys.argv",
            ["ataraxia", "--sink", "showcase.py", "--shards-dir", "samples"],
        ),
        patch("ataraxia.cli.backtest_dir", return_value=()) as backtest_dir,
        pytest.raises(SystemExit) as raised,
    ):
        main()

    captured = capsys.readouterr()

    assert raised.value.code == 1
    assert captured.err == "No backtest completed, check params and output file\n"
    backtest_dir.assert_called_once_with(Path("showcase.py"), Path("samples"))
