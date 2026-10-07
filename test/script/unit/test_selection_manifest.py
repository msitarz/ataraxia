# SPDX-License-Identifier: Apache-2.0
"""Verify complete manifest values and consumed JSON shape boundaries."""

import json
from pathlib import Path

import pytest

from script.registry_selection import Package, Selection
from test.script.record_variants import Json
from test.script.selection_manifest import ManifestObservation, read_manifest

EMPTY: dict[str, Json] = {
    "files": {},
    "links": {},
    "packages": [],
    "preparation_sha256": "anchor",
    "condition": {},
}
PACKAGE: dict[str, Json] = {
    "root": "r",
    "name": "n",
    "version": "v",
    "origin": "o",
    "wheel": "w",
    "archive": "a",
    "basis": "b",
    "trace": "t",
}


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-observations/manifest-adaptation/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-observations/README.md",
    ac="AC-1",
)
def test_manifest_retains_every_literal_public_value() -> None:
    """Given literal or delivered manifest data, observations retain
    every public value through precise canonical types and reject malformed
    consumed shapes before exposing typed values; real public selector calls
    preserve the independent complete expected result and input state.

    Given prepared inputs, actual selector/CLI observations retain
    complete manifest fields, file bytes/link targets, exit and diagnostics
    through precisely typed results.

    Parent coverage verifies complete canonical manifest values and unchanged
    literal source bytes; selector and process behavior are covered separately.

    This case covers complete reader values and source immutability.
    """
    # Given
    path = Path(__file__).parents[1] / "fixtures/manifest-observation.json"
    before = path.read_bytes()
    expected = ManifestObservation(
        Selection(
            {"relative.txt": "reviewed-digest"},
            {"linked": "target"},
            (
                Package(
                    "cache-root",
                    "package-name",
                    "package-version",
                    "package-origin",
                    "wheel-path",
                    "archive-path",
                    "review-basis",
                    "trace-path",
                ),
            ),
            "accepted-anchor",
        ),
        {"mode": "supported"},
    )

    # When
    result = read_manifest(path)

    # Then
    assert result == expected
    assert path.read_bytes() == before


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-observations/manifest-adaptation/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    ("document", "reason"),
    [
        ([], "selection manifest must contain exactly the five public fields"),
        ({}, "selection manifest must contain exactly the five public fields"),
        (
            {**EMPTY, "extra": "x"},
            "selection manifest must contain exactly the five public fields",
        ),
        ({**EMPTY, "files": []}, "selection manifest files must be a string map"),
        (
            {**EMPTY, "links": {"link": False}},
            "selection manifest links must be a string map",
        ),
        (
            {**EMPTY, "condition": {"mode": 1}},
            "selection manifest condition must be a string map",
        ),
        ({**EMPTY, "packages": {}}, "selection manifest packages must be a list"),
        (
            {**EMPTY, "packages": [{}]},
            "selection manifest package must contain exactly eight public fields",
        ),
        (
            {**EMPTY, "packages": [{**PACKAGE, "extra": "x"}]},
            "selection manifest package must contain exactly eight public fields",
        ),
        (
            {**EMPTY, "packages": [{**PACKAGE, "version": 1}]},
            "selection manifest package must be a string map",
        ),
        (
            {**EMPTY, "preparation_sha256": 1},
            "selection manifest preparation_sha256 must be a string",
        ),
    ],
    ids=[
        "non-object-manifest",
        "missing-public-fields",
        "extra-public-field",
        "files-not-map",
        "link-target-not-string",
        "condition-value-not-string",
        "packages-not-list",
        "missing-package-fields",
        "extra-package-field",
        "package-version-not-string",
        "preparation-digest-not-string",
    ],
)
def test_manifest_rejects_malformed_consumed_shapes(
    tmp_path: Path, document: Json, reason: str
) -> None:
    """Given literal or delivered manifest data, observations retain
    every public value through precise canonical types and reject malformed
    consumed shapes before exposing typed values; real public selector calls
    preserve the independent complete expected result and input state.

    This case covers exact consumed-shape refusal without source mutation.
    """
    # Given
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(document))
    before = path.read_bytes()

    # When
    with pytest.raises(ValueError) as error:
        read_manifest(path)

    # Then
    assert error.value.args == (reason,)
    assert error.value.__cause__ is None
    assert path.read_bytes() == before
