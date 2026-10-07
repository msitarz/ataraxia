# SPDX-License-Identifier: Apache-2.0
"""Keep changed-input and record-fixture domains distinct at typed callers."""

from pathlib import Path
from typing import assert_type

from test.script.selection_inputs import (
    ChangedInput,
    PreparedSelection,
    RecordName,
    arrange_changed_input,
    changed_input_name,
    copy_selection_fixture,
    record_fixture_name,
)


def check_named_input_contracts(
    case: PreparedSelection, directory: Path, change: ChangedInput, record: RecordName
) -> None:
    assert_type(changed_input_name("file"), ChangedInput)
    assert_type(record_fixture_name("uv"), RecordName)
    arrange_changed_input(case, changed_input_name("file"))
    copy_selection_fixture(directory, record_fixture_name("uv"))
    arrange_changed_input(case, record)  # E: is not assignable
    copy_selection_fixture(directory, change)  # E: is not assignable
    arrange_changed_input(case, "uv")  # E: is not assignable
    copy_selection_fixture(directory, "file")  # E: is not assignable
