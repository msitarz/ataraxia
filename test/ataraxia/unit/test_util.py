# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz


from pathlib import Path

import pytest

from ataraxia.errors import ModuleError
from ataraxia.util import import_file


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/backtest/loading/README.md",
    ac="AC-1",
)
def test_import_file_raise(tmp_path: Path) -> None:
    """Retain the missing-basename refusal and its exact module error."""
    # Given
    missing_path = tmp_path / "i do not exist"
    assert not missing_path.exists()

    # When
    with pytest.raises(ModuleError, match=r"^Cannot load module$") as error:
        import_file(missing_path)

    # Then
    assert error.value.__cause__ is None
