# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from pathlib import Path

from ataraxia.util import import_file


def test_import_file(tmp_path: Path):
    mod_path = tmp_path / "example.py"

    mod_path.write_text(
        "from ataraxia.bar import Bar\n"
        "def new_bar():\n"
        "    return Bar(timestamp=1, open=1, high=1, low=1, close=1, volume=1)\n"
    )

    module = import_file(mod_path)

    assert module.new_bar().close == 1
