# SPDX-License-Identifier: Apache-2.0
"""Precisely observe manifest values and the public registry selector."""

from dataclasses import dataclass
import json
from pathlib import Path

import pytest

from script.registry_selection import Package, Selection, select
from test.script.record_variants import Json, json_value
from test.script.selection_inputs import PreparedSelection

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ManifestObservation:
    """All documented values of the delivered registry manifest."""

    selection: Selection
    condition: dict[str, str]


def string_map(value: Json, field: str) -> dict[str, str]:
    """Validate a consumed manifest object without production semantics.

    Returns:
        Complete string keys and string values.

    Raises:
        ValueError: If the consumed field is not a string map.
    """
    if not isinstance(value, dict):
        raise ValueError(f"selection manifest {field} must be a string map")
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(item, str):
            raise ValueError(f"selection manifest {field} must be a string map")
        result[key] = item
    return result


def manifest_package(value: Json) -> Package:
    """Adapt precisely the eight public package fields.

    Returns:
        A canonical public package value.

    Raises:
        ValueError: If public package fields are missing, extra or not strings.
    """
    if not isinstance(value, dict) or value.keys() != {
        "root",
        "name",
        "version",
        "origin",
        "wheel",
        "archive",
        "basis",
        "trace",
    }:
        raise ValueError(
            "selection manifest package must contain exactly eight public fields"
        )
    return Package(**string_map(value, "package"))


def read_manifest(path: Path) -> ManifestObservation:
    """Adapt complete public artifact values without deriving expected answers.

    Returns:
        Every public field through precise canonical value types.

    Raises:
        ValueError: If consumed manifest fields have missing/extra/wrong shapes.
    """
    decoded: object = json.loads(path.read_text())
    data = json_value(decoded)
    if not isinstance(data, dict) or data.keys() != {
        "files",
        "links",
        "packages",
        "preparation_sha256",
        "condition",
    }:
        raise ValueError(
            "selection manifest must contain exactly the five public fields"
        )
    package_data = data["packages"]
    if not isinstance(package_data, list):
        raise ValueError("selection manifest packages must be a list")
    digest = data["preparation_sha256"]
    if not isinstance(digest, str):
        raise ValueError("selection manifest preparation_sha256 must be a string")
    return ManifestObservation(
        Selection(
            string_map(data["files"], "files"),
            string_map(data["links"], "links"),
            tuple(manifest_package(item) for item in package_data),
            digest,
        ),
        string_map(data["condition"], "condition"),
    )


def expected_manifest() -> ManifestObservation:
    """Load the independently reviewed literal expected artifact.

    Returns:
        Whole expected manifest values, without production selection.
    """
    return read_manifest(
        ROOT / "test/script/fixtures/registry_selection/expected-selection.json"
    )


def expected_selection() -> Selection:
    """Return the independent literal selector expectation."""
    return expected_manifest().selection


def select_prepared(case: PreparedSelection) -> Selection:
    """Call the actual public selector with fixture paths.

    Returns:
        The unadapted canonical selector result.
    """
    return select(case.cache, case.record, case.accepted_sha256, case.repository)


@pytest.fixture
def selection_expected() -> Selection:
    """Provide the independent whole selector expectation."""
    return expected_selection()


@pytest.fixture
def manifest_expected() -> ManifestObservation:
    """Provide the independent whole manifest expectation."""
    return expected_manifest()
