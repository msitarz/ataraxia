# SPDX-License-Identifier: Apache-2.0
from typing import Literal, TypeIs, get_args

type ChangedInput = Literal["declaration", "file"]
type RecordName = Literal["accepted", "version"]


def is_changed_input(value: str) -> TypeIs[ChangedInput]:
    return value in get_args(ChangedInput.__value__)


def is_record_name(value: str) -> TypeIs[RecordName]:
    return value in get_args(RecordName.__value__)


def changed_input(value: object) -> ChangedInput:
    if not isinstance(value, str):
        raise ValueError("changed input must be a string")
    if not is_changed_input(value):
        raise ValueError("unsupported changed input")
    return value


def record_name(value: object) -> RecordName:
    if not isinstance(value, str):
        raise ValueError("record name must be a string")
    if not is_record_name(value):
        raise ValueError("unsupported record name")
    return value


def consume_changed_input(value: ChangedInput) -> str:
    return f"changed:{value}"


def describe_change(value: ChangedInput) -> str:
    match value:
        case "declaration":
            return "update declaration"
        case "file":
            return "replace file"


def static_examples(open_value: str) -> None:
    consume_changed_input(changed_input("file"))
    consume_changed_input(open_value)  # E: is not assignable
    consume_changed_input("future-option")  # E: is not assignable
