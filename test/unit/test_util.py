# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz


import pytest

from ataraxia.errors import ModuleError
from ataraxia.util import import_file


def test_import_file_raise():
    with pytest.raises(ModuleError):
        import_file("i do not exist")
