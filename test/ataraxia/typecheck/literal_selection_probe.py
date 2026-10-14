# SPDX-License-Identifier: Apache-2.0
from enum import Enum
from typing import Literal, assert_type

type Change = Literal["declaration", "evidence", "file", "link", "record"]


class OutputKind(Enum):
    JSON = "json"
    TEXT = "text"


def accepted(value: str) -> Change:
    match value:
        case "declaration" | "evidence" | "file" | "link" | "record":
            return value
        case _:
            raise ValueError(value)


def examples(external: str, change: Change, kind: OutputKind) -> None:
    assert_type(change, Change)
    assert_type(kind, OutputKind)
    accepted(external)
    narrowed = accepted(external)
    assert_type(narrowed, Change)
    # A finite-domain caller must validate the open external string first.
    consume_change(external)  # E: is not assignable
    consume_change(change)


def consume_change(value: Change) -> None:
    pass


def invalid_change_result() -> Change:
    return "future-option"  # E: is not assignable
