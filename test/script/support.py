# SPDX-License-Identifier: Apache-2.0
"""Small process fixtures for the repository's registry selection boundary."""

from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys

from script.registry_selection import (
    Package,
    Selection,
    select,
)
from script.registry_selection import (
    PackagePayload as PackagePayload,
)
from script.registry_selection import (
    accepted_preparation as accepted_preparation,
)
from script.registry_selection import (
    dependency_declarations as dependency_declarations,
)
from script.registry_selection import (
    package_payload as package_payload,
)
from script.registry_selection import (
    preparation_evidence as preparation_evidence,
)
from script.registry_selection import (
    validate_digest as validate_digest,
)
from script.registry_selection import (
    validate_package_layout as validate_package_layout,
)
from script.registry_selection import (
    validate_payload_metadata as validate_payload_metadata,
)
from script.registry_selection import (
    validate_selected_inventory as validate_selected_inventory,
)
from script.registry_selection import (
    validate_wheel_link as validate_wheel_link,
)
from test.script.selection_inputs import PreparedSelection

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ManifestObservation:
    """All documented values of the delivered registry manifest."""

    selection: Selection
    condition: dict[str, str]


@dataclass(frozen=True)
class SelectionProcessResult:
    """Actual CLI process outcome and retained artifact bytes."""

    exit_code: int
    stdout: str
    stderr: str
    manifest: ManifestObservation | None
    failure: str | None
    destination_exists: bool
    source_after: dict[str, bytes | str]
    destination_after: dict[str, bytes | str]

    @property
    def output(self) -> str:
        """Return combined process diagnostics."""
        return self.stdout + self.stderr


def expected_selection() -> Selection:
    """Read an independent whole expected value from a literal fixture.

    Returns:
        The expected public selector result.
    """
    return expected_manifest().selection


def read_manifest(path: Path) -> ManifestObservation:
    """Read public artifact values without deriving expected answers.

    Returns:
        All documented manifest fields.

    Raises:
        ValueError: If the manifest has missing or unexpected top-level fields.
    """
    data = json.loads(path.read_text())
    if data.keys() != {
        "files",
        "links",
        "packages",
        "preparation_sha256",
        "condition",
    }:
        raise ValueError(
            "selection manifest must contain exactly the five public fields"
        )
    result = Selection(
        data["files"],
        data["links"],
        tuple(Package(**record) for record in data["packages"]),
        data["preparation_sha256"],
    )
    return ManifestObservation(result, data["condition"])


def expected_manifest() -> ManifestObservation:
    """Load an independent literal expected artifact.

    Returns:
        Whole expected manifest values.
    """
    return read_manifest(
        ROOT / "test/script/fixtures/registry_selection/expected-selection.json"
    )


def select_prepared(case: PreparedSelection) -> Selection:
    """Call the actual public selector with fixture paths.

    Returns:
        The public selector's result without adapting its behavior.
    """
    return select(case.cache, case.record, case.accepted_sha256, case.repository)


def tree_state(directory: Path) -> dict[str, bytes | str]:
    """Observe file bytes and link targets without following links.

    Returns:
        A complete relative-entry state snapshot.
    """
    state: dict[str, bytes | str] = {}
    for path in directory.rglob("*"):
        if path.is_symlink():
            state[path.relative_to(directory).as_posix()] = str(path.readlink())
        elif path.is_file():
            state[path.relative_to(directory).as_posix()] = path.read_bytes()
    return state


def run_selection_cli(case: PreparedSelection) -> SelectionProcessResult:
    """Invoke the actual repository CLI at its subprocess boundary.

    Returns:
        Exit status, diagnostics and retained output/input observations.
    """
    scratch = case.directory / "process-tmp"
    scratch.mkdir()
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "script/registry_selection.py"),
            "--cache",
            str(case.cache),
            "--record",
            str(case.record),
            "--expected",
            case.accepted_sha256,
            "--destination",
            str(case.destination),
        ],
        cwd=case.repository,
        env={
            "PATH": f"{Path(sys.executable).parent}:/usr/bin:/bin",
            "TMPDIR": str(scratch),
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    manifest, failure = (
        case.destination / "selection.json",
        case.destination / "failure.txt",
    )
    return SelectionProcessResult(
        process.returncode,
        process.stdout,
        process.stderr,
        read_manifest(manifest) if manifest.is_file() else None,
        failure.read_text() if failure.is_file() else None,
        case.destination.exists(),
        tree_state(case.cache),
        tree_state(case.destination),
    )


@dataclass
class ChangingRecordRead:
    """Honest filesystem edge: a later record read sees a different fixture file."""

    record: Path
    replacement: Path
    reader: Callable[[Path], bytes]
    record_reads: int = 0

    def read(self, path: Path) -> bytes:
        """Delegate actual file reads, changing only the second record read."""
        if path == self.record:
            self.record_reads += 1
            if self.record_reads > 1:
                return self.reader(self.replacement)
        return self.reader(path)
