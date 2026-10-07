# SPDX-License-Identifier: Apache-2.0
"""Verify complete named record changes and fixture-byte preservation."""

import hashlib
from pathlib import Path

import pytest

from test.script.record_variants import arrange_record_variant, read_fixture
from test.script.selection_inputs import RecordName, copy_selection_fixture
from test.script.support import ROOT, tree_state


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-inputs/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-inputs/record-variants/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    ("name", "expected_digest"),
    [
        (
            "accepted",
            "86a0bd7e2b6004ca8deaaf776b1f344fa65b1531ccf3585a423635d14f559cff",
        ),
        ("uv", "aafe6af464733745676ab85e32d56ad890c809b663ff38913d6abf0b9cf2f9d2"),
        ("index", "2ea9207424d03cb679097145d905db0bc9f9d9ea52f27e6a27465cb9a0a1d12b"),
        (
            "platform",
            "25a71a3777af75e71a78db438c75b3cfc7e4f7aa87f1d28cc1f4b4b709cc7e59",
        ),
        ("layout", "eb1f9435661f1907be18bd0ee2f962d74ccda9c7a8dddb9c660f6a2ecab53dee"),
        (
            "metadata",
            "7857ca93aa9485fb10f163d3d48c7430d0c46a948fd2f417e9ce96c6cd712955",
        ),
        (
            "undeclared",
            "3f23c33961228e603bfe2de6dddb5e0c025a11434661ac4c973a748b86561942",
        ),
        ("version", "c1cb3c41c345e565842135df4ce94e7acc40fc770da1316d1f3cd113e84e3f8c"),
    ],
    ids=[
        "accepted",
        "uv",
        "index",
        "platform",
        "layout",
        "metadata",
        "undeclared",
        "version",
    ],
)
def test_named_record_bytes_and_acceptance_digest_are_preserved(
    tmp_path: Path, name: RecordName, expected_digest: str
) -> None:
    """Given fresh accepted record copies and each of the seven named
    variants, preparation changes only the named record fields, retains all other
    values and source fixture bytes, and preserves the reviewed acceptance digest
    for accepted input and the changed-byte digest for variant input.

    Given fresh accepted or damaged named inputs, arrangements
    expose precisely typed paths/data and the independent preparation acceptance
    digest without changing shared source fixtures.

    Parent coverage verifies complete record bytes/digests and source immutability;
    typed paths and filesystem/copy isolation are covered by companion cases.

    Covers all eight complete serialized records, digest forwarding and source
    immutability; the companion case checks untouched recursive JSON values.
    """
    # Given
    fixtures = ROOT / "test/script/fixtures/registry_selection"
    before = tree_state(fixtures)
    # Literal digests freeze accepted bytes and seven independently specified
    # field changes, including ordering, indentation and the trailing newline.

    # When
    result = copy_selection_fixture(tmp_path, name)

    # Then
    assert hashlib.sha256(result.record.read_bytes()).hexdigest() == expected_digest
    assert result.accepted_sha256 == expected_digest
    assert tree_state(fixtures) == before


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-inputs/record-variants/README.md",
    ac="AC-1",
)
def test_record_change_preserves_unconsumed_recursive_json(tmp_path: Path) -> None:
    """Given fresh accepted record copies and each of the seven named
    variants, preparation changes only the named record fields, retains all other
    values and source fixture bytes, and preserves the reviewed acceptance digest
    for accepted input and the changed-byte digest for variant input.

    Covers preservation of untouched supported JSON values without imposing the
    production record schema; named records/digests are covered separately.
    """
    # Given
    record = tmp_path / "record.json"
    record.write_text(
        '{"condition":{"uv":"supported"},'
        '"untouched":[null,true,7,1.5,"text",{"nested":[false]}]}'
    )
    variant = tmp_path / "uv.json"
    variant.write_text('{"condition":{"uv":"unsupported"}}')

    # When
    arrange_record_variant(record, variant)

    # Then
    assert read_fixture(record) == {
        "condition": {"uv": "unsupported"},
        "untouched": [None, True, 7, 1.5, "text", {"nested": [False]}],
    }
    assert variant.read_text() == '{"condition":{"uv":"unsupported"}}'
