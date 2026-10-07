# SPDX-License-Identifier: Apache-2.0
"""Real selection CLI execution and complete filesystem observations."""

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from tempfile import mkdtemp

from test.script.selection_inputs import PreparedSelection
from test.script.selection_manifest import ManifestObservation, read_manifest

ROOT = Path(__file__).resolve().parents[2]


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
    inputs_after: dict[str, bytes | str]
    environment: dict[str, str]

    @property
    def output(self) -> str:
        """Return combined process diagnostics."""
        return self.stdout + self.stderr


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
    process_root = Path(mkdtemp(prefix="selection-process-", dir=case.directory.parent))
    home, scratch = process_root / "home", process_root / "tmp"
    home.mkdir()
    scratch.mkdir()
    environment = {
        "PATH": f"{Path(sys.executable).parent}:/usr/bin:/bin",
        "HOME": str(home),
        "TMPDIR": str(scratch),
    }
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
        env=environment,
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
        tree_state(case.directory),
        environment,
    )
