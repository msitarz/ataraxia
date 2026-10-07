# SPDX-License-Identifier: Apache-2.0
"""Fresh literal filesystem arrangements for registry selection consumers."""

from dataclasses import dataclass, replace
import hashlib
from pathlib import Path
import shutil

import pytest

from test.script.record_variants import arrange_record_variant

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class PreparedSelection:
    """Copied literal preparation input, independent of production constants."""

    directory: Path
    cache: Path
    repository: Path
    record: Path
    accepted_sha256: str
    destination: Path


def copy_selection_fixture(directory: Path, record_name: str) -> PreparedSelection:
    """Build literal preparation inputs and copy the accepted record.

    Returns:
        Paths and a separately frozen acceptance digest.
    """
    fixtures = ROOT / "test/script/fixtures/registry_selection"
    build_selection_inputs(directory)
    record = directory / "record.json"
    shutil.copyfile(fixtures / "records/accepted.json", record)
    accepted_sha256 = (fixtures / "accepted-sha256.txt").read_text().strip()
    if record_name != "accepted":
        arrange_record_variant(record, fixtures / "variants" / f"{record_name}.json")
        accepted_sha256 = hashlib.sha256(record.read_bytes()).hexdigest()
    return PreparedSelection(
        directory,
        directory / "cache",
        directory / "repository",
        directory / "record.json",
        accepted_sha256,
        directory / "result",
    )


def build_selection_inputs(directory: Path) -> None:
    """Build the tiny synthetic preparation filesystem from explicit bytes."""
    files = {
        "successful-setup.log": b"fixture preparation evidence\n",
        "repository/uv.lock": b"# frozen fixture declaration\n",
        "repository/pyproject.toml": b"# frozen fixture declaration\n",
        "repository/.pre-commit-config.yaml": (
            b"# frozen fixture declaration\nrepos: []\n"
        ),
        "cache/answers": b"project answer\n",
        "cache/uv/interpreter-v4/environment": b"old environment\n",
        "cache/uv/sdists-v9/editable/project.whl": b"project editable payload\n",
        "cache/prek/cache/uv/simple-v25/pypi/dependency.rkyv": (
            b"opaque fixture simple record\n"
        ),
    }
    for root in ("cache/uv", "cache/prek/cache/uv"):
        files[f"{root}/archive-v0/dependency/payload.txt"] = b"pinned fixture payload\n"
        files[f"{root}/archive-v0/dependency/dependency-1.0.dist-info/METADATA"] = (
            b"Name: dependency\nVersion: 1.0\n"
        )
        files[f"{root}/wheels-v6/pypi/dependency/1.0-py3-none-any.http"] = (
            b"opaque fixture HTTP record\n"
        )
    for name, contents in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
    for root in ("cache/uv", "cache/prek/cache/uv"):
        link = directory / root / "wheels-v6/pypi/dependency/1.0-py3-none-any"
        link.symlink_to("../../../archive-v0/dependency")


def arrange_changed_input(case: PreparedSelection, change: str) -> None:
    """Arrange one damaged external input using real fixture files."""
    changed = ROOT / "test/script/fixtures/registry_selection/changed.txt"
    destinations = {
        "declaration": case.repository / "uv.lock",
        "evidence": case.directory / "successful-setup.log",
    }
    match change:
        case "declaration" | "evidence":
            shutil.copyfile(changed, destinations[change])
        case "file":
            (case.cache / "uv/archive-v0/dependency/payload.txt").unlink()
        case "link":
            link = case.cache / "uv/wheels-v6/pypi/dependency/1.0-py3-none-any"
            link.unlink()
            link.symlink_to(case.repository)
        case "record":
            shutil.copyfile(
                ROOT / "test/script/fixtures/registry_selection/unapproved.json",
                case.record,
            )
        case _:
            raise ValueError(f"unknown fixture input: {change}")


def arrange_cli_collision(case: PreparedSelection) -> None:
    """Arrange a real preexisting result directory with a sentinel file."""
    case.destination.mkdir()
    shutil.copyfile(
        ROOT / "test/script/fixtures/registry_selection/changed.txt",
        case.destination / "sentinel.txt",
    )


def parameter_name(request: pytest.FixtureRequest) -> str:
    """Validate pytest's untyped parameter at the owned fixture boundary.

    Returns:
        The named arrangement selected by the parametrized consumer.

    Raises:
        ValueError: If the external pytest parameter is not a name.
    """
    value: object = request.param
    if not isinstance(value, str):
        raise ValueError("selection fixture parameter must be a name")
    return value


@pytest.fixture
def prepared_selection(tmp_path: Path) -> PreparedSelection:
    """Provide a fresh accepted preparation filesystem."""
    return copy_selection_fixture(tmp_path, "accepted")


@pytest.fixture
def changed_selection(
    request: pytest.FixtureRequest, prepared_selection: PreparedSelection
) -> PreparedSelection:
    """Damage only the named input in a fresh arrangement."""
    arrange_changed_input(prepared_selection, parameter_name(request))
    return prepared_selection


@pytest.fixture
def unsupported_selection(
    request: pytest.FixtureRequest, tmp_path: Path
) -> PreparedSelection:
    """Provide a fresh named unsupported record variant."""
    return copy_selection_fixture(tmp_path, parameter_name(request))


@pytest.fixture
def cli_missing_record(prepared_selection: PreparedSelection) -> PreparedSelection:
    """Select an absent record without changing the accepted fixture."""
    return replace(
        prepared_selection, record=prepared_selection.directory / "absent.json"
    )


@pytest.fixture
def cli_existing_destination(
    prepared_selection: PreparedSelection,
) -> PreparedSelection:
    """Provide a preexisting destination with independently reviewed bytes."""
    arrange_cli_collision(prepared_selection)
    return prepared_selection


@pytest.fixture
def cli_cache_destination(
    prepared_selection: PreparedSelection,
) -> PreparedSelection:
    """Select a forbidden cache-contained destination."""
    return replace(
        prepared_selection, destination=prepared_selection.cache / "forbidden"
    )
