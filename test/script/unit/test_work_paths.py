# SPDX-License-Identifier: Apache-2.0
"""Check Work path resolution against generated and named filesystem cases."""

import os
from pathlib import Path
import string
import tempfile

from hypothesis import example, given
from hypothesis import strategies as st
import pytest

from script.work_paths import resolve_work_file

_SEGMENT_CHARACTERS = string.ascii_letters + string.digits + "_-"


@pytest.mark.covers(
    work="doc/feat/testing-conformance/hypothesis/workpaths/README.md", ac="AC-1"
)
@given(
    segments=st.lists(
        st.text(alphabet=_SEGMENT_CHARACTERS, min_size=1, max_size=8),
        min_size=1,
        max_size=3,
    ),
    filename=st.sampled_from(("README.md", "spec.md")),
)
@example(segments=["W"], filename="README.md")
@example(segments=["a_b", "9-x", "Z"], filename="spec.md")
def test_resolve_work_file_accepts_generated_canonical_paths(
    segments: list[str], filename: str
) -> None:
    """Accept generated existing contracts and return their resolved identity."""
    # Given
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        relative = Path(*segments, filename)
        contract = root / relative
        contract.parent.mkdir(parents=True)
        contract.write_text("# Temporary Work\n", encoding="utf-8")

        # When
        resolved = resolve_work_file(root, relative.as_posix())

        # Then
        assert resolved == contract.resolve()


@pytest.mark.parametrize(
    ("work", "message"),
    [
        (
            "",
            "WORK is required; provide a repo-relative README.md or spec.md path",
        ),
        (
            "/absolute/README.md",
            "WORK must be a repo-relative README.md or spec.md path",
        ),
        ("../README.md", "WORK must be a normalized repo-relative path"),
        ("contracts/./README.md", "WORK must be a normalized repo-relative path"),
        ("contracts//README.md", "WORK must be a normalized repo-relative path"),
        (
            "contracts/bad space/README.md",
            "WORK must be a repo-relative README.md or spec.md path",
        ),
        (
            "contracts/README.txt",
            "WORK must name an owning README.md or spec.md",
        ),
        (
            "absent/README.md",
            "WORK does not identify an existing repository file: absent/README.md",
        ),
    ],
    ids=[
        "empty",
        "absolute",
        "parent-traversal",
        "dot-component",
        "repeated-separator",
        "invalid-character",
        "wrong-suffix",
        "absent-file",
    ],
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/hypothesis/workpaths/README.md", ac="AC-1"
)
def test_resolve_work_file_rejects_named_invalid_paths(
    tmp_path: Path, work: str, message: str
) -> None:
    """Reject named malformed and absent paths with their exact reason."""
    # Given
    # The fresh root has no Work contract files.

    # When
    with pytest.raises(ValueError) as raised:
        resolve_work_file(tmp_path, work)

    # Then
    assert type(raised.value) is ValueError
    assert raised.value.args == (message,)
    assert raised.value.__cause__ is None


@pytest.mark.parametrize("inside", [True, False], ids=["inside", "outside"])
@pytest.mark.covers(
    work="doc/feat/testing-conformance/hypothesis/workpaths/README.md", ac="AC-1"
)
def test_resolve_work_file_handles_relative_symlinks(
    tmp_path: Path, inside: bool
) -> None:
    """Accept contained relative links and refuse links escaping the root."""
    # Given
    root = tmp_path / "repository"
    root.mkdir()
    target = (
        root / "contracts" / "README.md"
        if inside
        else tmp_path / "outside" / "README.md"
    )
    target.parent.mkdir(parents=True)
    target.write_text("# Link target\n", encoding="utf-8")
    link = root / "linked" / "README.md"
    link.parent.mkdir()
    relative_target = Path(os.path.relpath(target, link.parent))
    try:
        link.symlink_to(relative_target)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"relative file symlinks are unavailable: {error}")

    # When
    if inside:
        resolved = resolve_work_file(root, "linked/README.md")

        # Then
        assert resolved == target.resolve()
    else:
        with pytest.raises(ValueError) as raised:
            resolve_work_file(root, "linked/README.md")

        # Then
        assert type(raised.value) is ValueError
        assert raised.value.args == (
            "WORK does not identify an existing repository file: linked/README.md",
        )
        assert raised.value.__cause__ is None
