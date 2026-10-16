# SPDX-License-Identifier: Apache-2.0
"""Exercise Work contract discovery through real repository files."""

from pathlib import Path

import pytest

from script.work_check.discovery import ContractDiscoveryError, discover_contracts


def _write_contract(
    root: Path, relative: str, text: str = "malformed on purpose\n"
) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_default_discovers_every_work_readme_without_content_heuristics(
    tmp_path: Path,
) -> None:
    # Given
    malformed_parent = _write_contract(tmp_path, "doc/feat/parent/README.md", "")
    investigation = _write_contract(
        tmp_path, "doc/feat/parent/investigation/README.md", "# Investigation\n"
    )
    _write_contract(tmp_path, "doc/feat/supporting/notes.md")
    _write_contract(tmp_path, "doc/guidance/README.md")
    _write_contract(tmp_path, "README.md")

    # When
    contracts = discover_contracts(tmp_path)

    # Then
    assert [(item.path, item.text) for item in contracts] == [
        (malformed_parent, ""),
        (investigation, "# Investigation\n"),
    ]


def test_explicit_overlapping_files_and_subtrees_are_deduplicated_and_sorted(
    tmp_path: Path,
) -> None:
    # Given
    earlier = _write_contract(tmp_path, "doc/feat/a/README.md")
    later = _write_contract(tmp_path, "doc/feat/z/README.md")

    # When
    contracts = discover_contracts(
        tmp_path,
        ("doc/feat/z/README.md", "doc/feat", "doc/feat/a"),
    )

    # Then
    assert tuple(item.path for item in contracts) == (earlier, later)


@pytest.mark.parametrize(
    ("selection", "message"),
    [
        pytest.param("README.md", "outside the Work root", id="outside-root"),
        pytest.param(
            "doc/feat/../../outside/README.md",
            "outside the Work root",
            id="traversal-outside-root",
        ),
        pytest.param("doc/feat/notes.md", "not a Work contract", id="non-contract"),
    ],
)
def test_invalid_explicit_selections_fail_with_actionable_context(
    tmp_path: Path, selection: str, message: str
) -> None:
    # Given
    _write_contract(tmp_path, "doc/feat/notes.md")
    _write_contract(tmp_path, "README.md")
    _write_contract(tmp_path, "outside/README.md")

    # When
    with pytest.raises(ContractDiscoveryError) as error:
        discover_contracts(tmp_path, (selection,))

    # Then
    assert message in str(error.value)
    assert selection in str(error.value)


def test_missing_selection_preserves_filesystem_cause(tmp_path: Path) -> None:
    # Given
    _write_contract(tmp_path, "doc/feat/existing/README.md")
    selection = "doc/feat/missing"

    # When
    with pytest.raises(ContractDiscoveryError) as error:
        discover_contracts(tmp_path, (selection,))

    # Then
    assert selection in str(error.value)
    assert isinstance(error.value.__cause__, FileNotFoundError)


@pytest.mark.parametrize(
    "selections",
    [
        pytest.param(("doc/feat/empty",), id="empty-only"),
        pytest.param(
            ("doc/feat/valid/README.md", "doc/feat/empty"), id="mixed-valid-empty"
        ),
    ],
)
def test_explicit_subtree_without_contracts_fails_even_with_other_contracts(
    tmp_path: Path, selections: tuple[str, ...]
) -> None:
    # Given
    (tmp_path / "doc/feat/empty").mkdir(parents=True)
    _write_contract(tmp_path, "doc/feat/valid/README.md")

    # When
    with pytest.raises(ContractDiscoveryError) as error:
        discover_contracts(tmp_path, selections)

    # Then
    assert "Selection contains no Work contract" in str(error.value)
    assert "doc/feat/empty" in str(error.value)


def test_recursive_discovery_skips_linked_directories(tmp_path: Path) -> None:
    # Given
    outside = tmp_path / "outside"
    outside.mkdir()
    _write_contract(tmp_path, "outside/README.md")
    work_root = tmp_path / "doc/feat"
    work_root.mkdir(parents=True)
    local = _write_contract(tmp_path, "doc/feat/local/README.md")
    (work_root / "escape").symlink_to(outside, target_is_directory=True)

    # When
    contracts = discover_contracts(tmp_path)

    # Then
    assert tuple(item.path for item in contracts) == (local,)


@pytest.mark.parametrize(
    "selections",
    [
        pytest.param((), id="default-root"),
        pytest.param(("doc/feat/alias",), id="selected-subtree"),
    ],
)
def test_recursive_discovery_accepts_an_in_root_contract_file_link(
    tmp_path: Path, selections: tuple[str, ...]
) -> None:
    # Given
    target = _write_contract(tmp_path, "doc/feat/target/README.md", "# In root\n")
    alias = tmp_path / "doc/feat/alias/README.md"
    alias.parent.mkdir(parents=True)
    alias.symlink_to(target)

    # When
    contracts = discover_contracts(tmp_path, selections)

    # Then
    assert tuple((item.path, item.text) for item in contracts) == (
        (target, "# In root\n"),
    )


def test_recursive_discovery_rejects_a_contract_link_outside_work_root(
    tmp_path: Path,
) -> None:
    # Given
    outside = _write_contract(tmp_path, "outside/README.md")
    alias = tmp_path / "doc/feat/alias/README.md"
    alias.parent.mkdir(parents=True)
    alias.symlink_to(outside)

    # When
    with pytest.raises(ContractDiscoveryError) as error:
        discover_contracts(tmp_path)

    # Then
    assert "escapes the Work root" in str(error.value)
    assert str(alias) in str(error.value)


def test_explicit_in_root_contract_link_is_accepted(tmp_path: Path) -> None:
    # Given
    target = _write_contract(tmp_path, "doc/feat/target/README.md")
    alias = tmp_path / "doc/feat/alias/README.md"
    alias.parent.mkdir(parents=True)
    alias.symlink_to(target)

    # When
    contracts = discover_contracts(tmp_path, ("doc/feat/alias/README.md",))

    # Then
    assert tuple(item.path for item in contracts) == (target,)


def test_explicit_link_alias_outside_work_root_is_rejected(tmp_path: Path) -> None:
    # Given
    target = _write_contract(tmp_path, "doc/feat/target/README.md")
    alias = tmp_path / "outside/README.md"
    alias.parent.mkdir()
    alias.symlink_to(target)

    # When
    with pytest.raises(ContractDiscoveryError) as error:
        discover_contracts(tmp_path, ("outside/README.md",))

    # Then
    assert "outside the Work root" in str(error.value)


def test_explicit_non_readme_link_to_a_contract_is_rejected(tmp_path: Path) -> None:
    # Given
    target = _write_contract(tmp_path, "doc/feat/target/README.md")
    alias = tmp_path / "doc/feat/alias.md"
    alias.symlink_to(target)

    # When
    with pytest.raises(ContractDiscoveryError) as error:
        discover_contracts(tmp_path, ("doc/feat/alias.md",))

    # Then
    assert "not a Work contract README.md" in str(error.value)


def test_explicit_contract_path_through_escaping_symlink_fails(
    tmp_path: Path,
) -> None:
    # Given
    outside = tmp_path / "outside"
    _write_contract(tmp_path, "outside/README.md")
    symlink = tmp_path / "doc/feat/escape"
    symlink.parent.mkdir(parents=True)
    symlink.symlink_to(outside, target_is_directory=True)
    selection = "doc/feat/escape/README.md"

    # When
    with pytest.raises(ContractDiscoveryError) as error:
        discover_contracts(tmp_path, (selection,))

    # Then
    assert "outside the Work root" in str(error.value)
    assert selection in str(error.value)


def test_unreadable_contract_fails_with_its_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    contract = _write_contract(tmp_path, "doc/feat/private/README.md")
    read_text = Path.read_text

    def deny_contract(
        path: Path, encoding: str | None = None, errors: str | None = None
    ) -> str:
        if path == contract:
            raise PermissionError("access denied")
        return read_text(path, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_text", deny_contract)

    # When
    with pytest.raises(ContractDiscoveryError) as error:
        discover_contracts(tmp_path, ("doc/feat/private/README.md",))

    # Then
    assert str(contract) in str(error.value)
    assert isinstance(error.value.__cause__, PermissionError)


def test_non_utf8_contract_fails_with_its_path_and_cause(tmp_path: Path) -> None:
    # Given
    contract = tmp_path / "doc/feat/invalid/README.md"
    contract.parent.mkdir(parents=True)
    contract.write_bytes(b"\xff")

    # When
    with pytest.raises(ContractDiscoveryError) as error:
        discover_contracts(tmp_path, ("doc/feat/invalid/README.md",))

    # Then
    assert str(contract) in str(error.value)
    assert isinstance(error.value.__cause__, UnicodeDecodeError)
