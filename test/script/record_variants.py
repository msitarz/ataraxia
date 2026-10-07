# SPDX-License-Identifier: Apache-2.0
"""Precisely adapt JSON at the named record-arrangement boundary."""

import json
from pathlib import Path

type Json = bool | int | float | str | list[Json] | dict[str, Json] | None


def json_value(value: object) -> Json:
    """Adapt decoded JSON without exposing unknown nested values.

    Returns:
        A scalar, list or string-keyed object containing supported JSON values.

    Raises:
        ValueError: If a value is outside the supported JSON contract.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [json_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, Json] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("record fixture JSON keys must be strings")
            result[key] = json_value(item)
        return result
    raise ValueError("record fixture contains an unsupported JSON value")


def json_object(value: Json, field: str) -> dict[str, Json]:
    """Require an object only at a field the arrangement consumes.

    Returns:
        The original mutable string-keyed object.

    Raises:
        ValueError: If the consumed field is not an object.
    """
    if not isinstance(value, dict):
        raise ValueError(f"record fixture {field} must be an object")
    return value


def json_string(value: Json, field: str) -> str:
    """Require a string only at a field the arrangement consumes.

    Returns:
        The original string.

    Raises:
        ValueError: If the consumed field is not a string.
    """
    if not isinstance(value, str):
        raise ValueError(f"record fixture {field} must be a string")
    return value


def read_fixture(path: Path) -> dict[str, Json]:
    """Read a JSON object while preserving all untouched fields.

    Returns:
        Precisely adapted fixture data, without production-record validation.
    """
    decoded: object = json.loads(path.read_text())
    return json_object(json_value(decoded), "root")


def arrange_record_variant(record: Path, description: Path) -> None:
    """Apply one named invalid fixture condition to a fresh accepted record.

    Raises:
        ValueError: If a consumed field has the wrong shape or variant is unknown.
    """
    data = read_fixture(record)
    variant = read_fixture(description)
    match description.stem:
        case "uv" | "index" | "platform" | "layout":
            json_object(data["condition"], "condition").update(
                json_object(variant["condition"], "variant condition")
            )
        case "metadata":
            files = json_object(data["files"], "files")
            del files[json_string(variant["remove_metadata"], "remove_metadata")]
        case "undeclared":
            json_object(data["files"], "files").update(
                json_object(variant["undeclared_file"], "undeclared_file")
            )
        case "version":
            packages = data["packages"]
            if not isinstance(packages, list) or not packages:
                raise ValueError("record fixture packages must be a nonempty list")
            json_object(packages[0], "first package")["version"] = json_string(
                variant["project_version"], "project_version"
            )
        case _:
            raise ValueError(f"unknown record variant: {description.stem}")
    record.write_text(json.dumps(data, indent=2) + "\n")
