# SPDX-License-Identifier: Apache-2.0
"""Single-source Literal inventories used by the Work's probes."""

from typing import Literal, TypeIs, get_args

type ChangedInput = Literal["declaration", "evidence", "file", "link", "record"]
type RecordName = Literal[
    "accepted", "uv", "index", "platform", "layout", "metadata", "undeclared", "version"
]


def is_changed_input(value: str) -> TypeIs[ChangedInput]:
    """Check membership in the ChangedInput alias's runtime metadata."""
    return value in get_args(ChangedInput.__value__)


def is_record_name(value: str) -> TypeIs[RecordName]:
    """Check membership in the RecordName alias's runtime metadata."""
    return value in get_args(RecordName.__value__)


def changed_input_name(value: str) -> ChangedInput:
    """Narrow a string or reject it, using the Literal as the inventory."""
    if not is_changed_input(value):
        raise ValueError(f"unknown fixture input: {value}")
    return value


def record_fixture_name(value: str) -> RecordName:
    """Narrow a string or reject it, using the Literal as the inventory."""
    if not is_record_name(value):
        raise ValueError(f"unknown record fixture: {value}")
    return value
