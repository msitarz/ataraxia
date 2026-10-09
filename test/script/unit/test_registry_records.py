# SPDX-License-Identifier: Apache-2.0
"""Verify literal registry record boundaries and precise refusal behavior."""

import json

import pytest

from script.registry_selection import (
    accepted_preparation,
    dependency_declarations,
    preparation_evidence,
    validate_digest,
)
from test.script.selection_inputs import ROOT


@pytest.fixture
def preparation_bytes() -> bytes:
    """Provide the checked-in accepted preparation record bytes."""
    return (
        ROOT / "test/script/fixtures/registry_selection/records/accepted.json"
    ).read_bytes()


@pytest.fixture
def preparation_expected() -> object:
    """Load the reviewed static record for complete equality."""
    path = ROOT / "test/script/fixtures/registry_selection/records/accepted.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/records/README.md",
    ac="AC-1",
)
def test_matching_digests_are_accepted() -> None:
    """Accept equal digest values without producing a result."""
    # Given
    actual = expected = "same"

    # When
    result = validate_digest(actual, expected, "changed input")

    # Then
    assert result is None


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/records/README.md",
    ac="AC-1",
)
def test_changed_digest_retains_context() -> None:
    """Raise the caller's exact digest context without chaining a cause."""
    # Given
    diagnostic = "changed selected file: payload"

    # When
    with pytest.raises(ValueError) as error:
        validate_digest("actual", "expected", diagnostic)

    # Then
    assert error.type is ValueError
    assert error.value.args == (diagnostic,)
    assert error.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/records/README.md",
    ac="AC-1",
)
def test_complete_declaration_inventory_is_returned() -> None:
    """Return the complete literal three-file declaration inventory."""
    # Given
    declarations = {
        "uv.lock": "lock",
        "pyproject.toml": "project",
        ".pre-commit-config.yaml": "hooks",
    }

    # When
    result = dependency_declarations(declarations)

    # Then
    assert result == {
        "uv.lock": "lock",
        "pyproject.toml": "project",
        ".pre-commit-config.yaml": "hooks",
    }


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/records/README.md",
    ac="AC-1",
)
def test_incomplete_declaration_inventory_is_rejected() -> None:
    """Reject a missing declaration with the exact error and no cause."""
    # Given
    declarations = {"uv.lock": "lock"}

    # When
    with pytest.raises(ValueError) as error:
        dependency_declarations(declarations)

    # Then
    assert error.type is ValueError
    assert error.value.args == ("incomplete dependency declarations",)
    assert error.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/records/README.md",
    ac="AC-1",
)
def test_reviewed_evidence_inventory_is_returned() -> None:
    """Return the complete reviewed evidence mapping unchanged."""
    # Given
    evidence = {"setup.log": "sha"}
    derivation = "reviewed derivation"

    # When
    result = preparation_evidence(evidence, derivation)

    # Then
    assert result == {"setup.log": "sha"}


@pytest.mark.parametrize(
    ("evidence", "derivation"),
    [
        pytest.param({}, "reviewed", id="absent-evidence"),
        pytest.param({"setup.log": "sha"}, "", id="absent-derivation"),
    ],
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/records/README.md",
    ac="AC-1",
)
def test_missing_reviewed_evidence_is_rejected(
    evidence: dict[str, str], derivation: str
) -> None:
    """Reject absent evidence or derivation with exact error and no cause."""
    # Given
    expected = "missing reviewed preparation evidence/derivation"

    # When
    with pytest.raises(ValueError) as error:
        preparation_evidence(evidence, derivation)

    # Then
    assert error.type is ValueError
    assert error.value.args == (expected,)
    assert error.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/records/README.md",
    ac="AC-1",
)
def test_supported_preparation_bytes_are_accepted(
    preparation_bytes: bytes,
    preparation_expected: object,
) -> None:
    """Accept the literal record bytes and retain every documented field."""
    # Given
    expected_digest = "86a0bd7e2b6004ca8deaaf776b1f344fa65b1531ccf3585a423635d14f559cff"

    # When
    result = accepted_preparation(preparation_bytes, expected_digest)

    # Then
    assert result == preparation_expected


@pytest.mark.parametrize(
    "expected",
    [
        pytest.param("not-a-digest", id="invalid-digest"),
        pytest.param(
            "0000000000000000000000000000000000000000000000000000000000000000",
            id="unaccepted-bytes",
        ),
    ],
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/records/README.md",
    ac="AC-1",
)
def test_unaccepted_preparation_bytes_are_rejected(
    preparation_bytes: bytes, expected: str
) -> None:
    """Reject malformed or unaccepted digests with exact error and no cause."""
    # Given
    diagnostic = "preparation digest differs from external acceptance"

    # When
    with pytest.raises(ValueError) as error:
        accepted_preparation(preparation_bytes, expected)

    # Then
    assert error.type is ValueError
    assert error.value.args == (diagnostic,)
    assert error.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/records/README.md",
    ac="AC-1",
)
def test_superfluous_declaration_key_is_rejected() -> None:
    """Reject an extra declaration key with the exact error and no cause."""
    # Given
    declarations = {
        "uv.lock": "lock",
        "pyproject.toml": "project",
        ".pre-commit-config.yaml": "hooks",
        "answer": "sha",
    }

    # When
    with pytest.raises(ValueError) as error:
        dependency_declarations(declarations)

    # Then
    assert error.type is ValueError
    assert error.value.args == ("incomplete dependency declarations",)
    assert error.value.__cause__ is None
