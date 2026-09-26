# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

import pytest

from ataraxia.backtest import backtest_dir


def test_backtest_dir_raise_on_wrong_param():
    with pytest.raises(FileNotFoundError):
        backtest_dir("hello", "i do not exist")
