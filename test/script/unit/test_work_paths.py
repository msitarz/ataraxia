# SPDX-License-Identifier: Apache-2.0
"""Check Work path resolution against generated and named filesystem cases."""

import os
from pathlib import Path
import string
import tempfile
from typing import Literal

from hypothesis import example, given
from hypothesis import strategies as st
import pytest

from script.work_paths import resolve_work_file

_SEGMENT_CHARACTERS = string.ascii_letters + string.digits + "_-"
_SEGMENT = st.text(alphabet=_SEGMENT_CHARACTERS, min_size=1, max_size=8)
_DIRECTORY_SEGMENTS = st.lists(_SEGMENT, min_size=1, max_size=2)
_CONTRACT_NAME = st.sampled_from(("README.md", "spec.md"))
type _InvalidWorkKind = Literal[
    "empty",
    "absolute",
    "parent-traversal",
    "dot-component",
    "repeated-separator",
    "invalid-character",
    "wrong-suffix",
    "absent-file",
]
_INVALID_WORK_KINDS: tuple[_InvalidWorkKind, ...] = (
    "empty",
    "absolute",
    "parent-traversal",
    "dot-component",
    "repeated-separator",
    "invalid-character",
    "wrong-suffix",
    "absent-file",
)


def _construct_invalid_work_path(
    segments: list[str], filename: str, kind: _InvalidWorkKind
) -> tuple[str, str]:
    """Build a named malformed input and its independent expected reason."""
    canonical = "/".join((*segments, filename))
    match kind:
        case "empty":
            return (
                "",
                "WORK is required; provide a repo-relative README.md or spec.md path",
            )
        case "absolute":
            return (
                f"/{canonical}",
                "WORK must be a repo-relative README.md or spec.md path",
            )
        case "parent-traversal" | "dot-component" | "repeated-separator":
            match kind:
                case "parent-traversal":
                    requested = f"../{canonical}"
                case "dot-component":
                    requested = f"./{canonical}"
                case "repeated-separator":
                    requested = canonical.replace("/", "//", 1)
            return requested, "WORK must be a normalized repo-relative path"
        case "invalid-character":
            requested = "/".join([segments[0], "bad space", *segments[1:], filename])
            return (
                requested,
                "WORK must be a repo-relative README.md or spec.md path",
            )
        case "wrong-suffix":
            return (
                "/".join([*segments, "wrong.txt"]),
                "WORK must name an owning README.md or spec.md",
            )
        case "absent-file":
            return (
                canonical,
                f"WORK does not identify an existing repository file: {canonical}",
            )


@pytest.mark.covers(
    work="doc/feat/testing-conformance/hypothesis/workpaths/README.md", ac="AC-1"
)
@given(
    segments=st.lists(_SEGMENT, min_size=1, max_size=3),
    filename=_CONTRACT_NAME,
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


@pytest.mark.covers(
    work="doc/feat/testing-conformance/hypothesis/workpaths/README.md", ac="AC-1"
)
@given(
    segments=st.lists(_SEGMENT, min_size=1, max_size=3),
    filename=_CONTRACT_NAME,
    kind=st.sampled_from(_INVALID_WORK_KINDS),
)
@example(segments=["A"], filename="README.md", kind="empty")
@example(segments=["A", "b"], filename="spec.md", kind="absolute")
@example(segments=["nested"], filename="README.md", kind="parent-traversal")
@example(segments=["folder", "inside"], filename="spec.md", kind="dot-component")
@example(segments=["folder"], filename="README.md", kind="repeated-separator")
@example(segments=["contracts", "abc"], filename="spec.md", kind="invalid-character")
@example(segments=["contracts"], filename="README.md", kind="wrong-suffix")
@example(segments=["missing", "contract"], filename="spec.md", kind="absent-file")
def test_resolve_work_file_rejects_generated_named_paths(
    segments: list[str], filename: str, kind: _InvalidWorkKind
) -> None:
    """Reject named malformed and absent paths with their exact reason."""
    # Given
    requested, reason = _construct_invalid_work_path(segments, filename, kind)
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)

        # When
        with pytest.raises(ValueError) as raised:
            resolve_work_file(root, requested)

        # Then
        assert type(raised.value) is ValueError
        assert raised.value.args == (reason,)
        assert raised.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/testing-conformance/hypothesis/workpaths/README.md", ac="AC-1"
)
@given(link_segments=_DIRECTORY_SEGMENTS, target_segments=_DIRECTORY_SEGMENTS)
@example(link_segments=["L"], target_segments=["T"])
@example(link_segments=["a_b", "9-x"], target_segments=["C", "d"])
def test_resolve_work_file_accepts_generated_inside_relative_symlinks(
    link_segments: list[str], target_segments: list[str]
) -> None:
    """Accept a relative symlink whose resolved contract stays inside root."""
    # Given
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        link_relative = Path("links", *link_segments, "README.md")
        target = root / Path("targets", *target_segments, "README.md")
        target.parent.mkdir(parents=True)
        target.write_text("# Contained target\n", encoding="utf-8")
        link = root / link_relative
        link.parent.mkdir(parents=True)
        relative_target = Path(os.path.relpath(target, start=link.parent))
        try:
            link.symlink_to(relative_target)
        except (NotImplementedError, OSError) as error:
            pytest.skip(f"relative file symlinks are unavailable: {error}")

        # When
        resolved = resolve_work_file(root, link_relative.as_posix())

        # Then
        assert resolved == target.resolve()


@pytest.mark.covers(
    work="doc/feat/testing-conformance/hypothesis/workpaths/README.md", ac="AC-1"
)
@given(link_segments=_DIRECTORY_SEGMENTS, target_segments=_DIRECTORY_SEGMENTS)
@example(link_segments=["L"], target_segments=["T"])
@example(link_segments=["a_b", "9-x"], target_segments=["C", "d"])
def test_resolve_work_file_rejects_generated_escaping_relative_symlinks(
    link_segments: list[str], target_segments: list[str]
) -> None:
    """Reject a relative symlink whose resolved contract escapes root."""
    # Given
    with (
        tempfile.TemporaryDirectory() as temporary_directory,
        tempfile.TemporaryDirectory() as outside_directory,
    ):
        root = Path(temporary_directory)
        outside = Path(outside_directory)
        link_relative = Path("links", *link_segments, "spec.md")
        target = outside / Path("targets", *target_segments, "spec.md")
        target.parent.mkdir(parents=True)
        target.write_text("# Escaping target\n", encoding="utf-8")
        link = root / link_relative
        link.parent.mkdir(parents=True)
        relative_target = Path(os.path.relpath(target, start=link.parent))
        try:
            link.symlink_to(relative_target)
        except (NotImplementedError, OSError) as error:
            pytest.skip(f"relative file symlinks are unavailable: {error}")

        # When
        with pytest.raises(ValueError) as raised:
            resolve_work_file(root, link_relative.as_posix())

        # Then
        assert type(raised.value) is ValueError
        assert raised.value.args == (
            "WORK does not identify an existing repository file: "
            f"{link_relative.as_posix()}",
        )
        assert raised.value.__cause__ is None
