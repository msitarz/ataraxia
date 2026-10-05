# SPDX-License-Identifier: Apache-2.0
"""Small process fixtures for the repository's registry selection boundary."""

from collections.abc import Callable
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from script.registry_selection import Package, Selection, select
else:
    script = Path(__file__).resolve().parents[1] / "script/registry_selection.py"
    spec = importlib.util.spec_from_file_location(
        "registry_selection_under_test", script
    )
    if spec is None or spec.loader is None:
        raise ImportError("cannot load the actual registry selector")
    selector = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = selector
    spec.loader.exec_module(selector)
    Package, Selection, select = selector.Package, selector.Selection, selector.select

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ("CACHE", "RECORD", "PREPARATION_SHA256", "DESTINATION")
VALUES = (
    "cache space's $(shell touch MAKE_PWNED)$(touch SHELL_PWNED)`touch TICK_PWNED`",
    "rec space's $(shell touch MAKE_PWNED)$(touch SHELL_PWNED)`touch TICK_PWNED`",
    "sha space's $(shell touch MAKE_PWNED)$(touch SHELL_PWNED)`touch TICK_PWNED`",
    "dest space's $(shell touch MAKE_PWNED)$(touch SHELL_PWNED)`touch TICK_PWNED`",
)
MARKERS = ("MAKE_PWNED", "SHELL_PWNED", "TICK_PWNED")


@dataclass(frozen=True)
class RegistryCase:
    """One prepared process invocation."""

    directory: Path
    environment: dict[str, str]
    assignments: tuple[str, ...]


@dataclass(frozen=True)
class RegistryInputs:
    """Observed named CLI values, independent of transport prefix and order."""

    cache: str
    record: str
    expected: str
    destination: str


@dataclass(frozen=True)
class ProcessResult:
    """Observed process output and filesystem state."""

    exit_code: int
    stdout: str
    stderr: str
    argv: tuple[str, ...]
    inputs: RegistryInputs | None
    markers: tuple[str, ...]
    destination_exists: bool

    @property
    def output(self) -> str:
        """Return stdout and stderr together for assertion diagnostics."""
        return self.stdout + self.stderr


def copy_registry_project(directory: Path) -> None:
    """Copy actual production artifacts and the external uv fixture."""
    shutil.copyfile(ROOT / "Makefile", directory / "Makefile")
    (directory / "script").mkdir()
    shutil.copyfile(
        ROOT / "script/registry_selection.py",
        directory / "script/registry_selection.py",
    )
    shutil.copyfile(ROOT / "test/fixtures/registry_uv.py", directory / "uv")
    (directory / "uv").chmod(0o755)


def registry_case(directory: Path, mode: str) -> RegistryCase:
    """Prepare explicit process inputs without inheriting caller flags.

    Returns:
        A literal-argument or missing-input case.
    """
    environment = {
        "PATH": f"{directory}:{Path(sys.executable).parent}:/usr/bin:/bin",
        "TMPDIR": str(directory),
        "UV_PROXY_MODE": mode,
    }
    assignments = tuple(
        f"{name}={value}" for name, value in zip(INPUTS, VALUES, strict=True)
    )
    if mode == "delegate":
        assignments = (f"DESTINATION={directory / 'result'}",)
    return RegistryCase(directory, environment, assignments)


def run_registry_target(case: RegistryCase) -> ProcessResult:
    """Run actual Make and observe delegated argv and untouched state.

    Returns:
        Captured output, exact exit code and filesystem observations.
    """
    process = subprocess.run(
        ["make", "registry-select", *case.assignments],
        cwd=case.directory,
        env=case.environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    log = case.directory / "argv.json"
    value: object = json.loads(log.read_text()) if log.exists() else []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("external uv log must contain string arguments")
    argv = tuple(cast(list[str], value))
    markers = tuple(name for name in MARKERS if (case.directory / name).exists())
    return ProcessResult(
        process.returncode,
        process.stdout,
        process.stderr,
        argv,
        observe_registry_inputs(argv),
        markers,
        (case.directory / "result").exists(),
    )


def observe_registry_inputs(argv: tuple[str, ...]) -> RegistryInputs | None:
    """Project named values out of the actual external process argv log.

    Returns:
        Named values when all four flags were observed, otherwise None.
    """
    flags = {"--cache", "--record", "--expected", "--destination"}
    observed = {
        argument: argv[index + 1]
        for index, argument in enumerate(argv[:-1])
        if argument in flags
    }
    if observed.keys() != flags:
        return None
    return RegistryInputs(
        observed["--cache"],
        observed["--record"],
        observed["--expected"],
        observed["--destination"],
    )


@dataclass(frozen=True)
class PreparedSelection:
    """Copied literal preparation input, independent of production constants."""

    directory: Path
    cache: Path
    repository: Path
    record: Path
    accepted_sha256: str
    destination: Path


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


def copy_selection_fixture(directory: Path, record_name: str) -> PreparedSelection:
    """Copy a static preparation tree and named literal record.

    Returns:
        Paths and a separately frozen acceptance digest.
    """
    fixtures = ROOT / "test/fixtures/registry_selection"
    shutil.copytree(fixtures / "common", directory, dirs_exist_ok=True, symlinks=True)
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


def arrange_record_variant(record: Path, description: Path) -> None:
    """Apply one named invalid fixture condition to a fresh accepted record."""
    data = json.loads(record.read_text())
    variant = json.loads(description.read_text())
    if description.stem in {"uv", "index", "platform", "layout"}:
        data["condition"].update(variant["condition"])
    elif description.stem == "metadata":
        del data["files"][variant["remove_metadata"]]
    elif description.stem == "undeclared":
        data["files"].update(variant["undeclared_file"])
    elif description.stem == "version":
        data["packages"][0]["version"] = variant["project_version"]
    else:
        raise ValueError(f"unknown record variant: {description.stem}")
    record.write_text(json.dumps(data, indent=2) + "\n")


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
        ROOT / "test/fixtures/registry_selection/expected-selection.json"
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


def arrange_changed_input(case: PreparedSelection, change: str) -> None:
    """Arrange one damaged external input using real fixture files."""
    changed = ROOT / "test/fixtures/registry_selection/changed.txt"
    destinations = {
        "declaration": case.repository / "uv.lock",
        "evidence": case.directory / "successful-setup.log",
    }
    if change in destinations:
        shutil.copyfile(changed, destinations[change])
    elif change == "file":
        (case.cache / "uv/archive-v0/dependency/payload.txt").unlink()
    elif change == "link":
        link = case.cache / "uv/wheels-v6/pypi/dependency/1.0-py3-none-any"
        link.unlink()
        link.symlink_to(case.repository)
    elif change == "record":
        shutil.copyfile(
            ROOT / "test/fixtures/registry_selection/unapproved.json", case.record
        )
    else:
        raise ValueError(f"unknown fixture input: {change}")


def arrange_cli_collision(case: PreparedSelection) -> None:
    """Arrange a real preexisting result directory with a sentinel file."""
    case.destination.mkdir()
    shutil.copyfile(
        ROOT / "test/fixtures/registry_selection/changed.txt",
        case.destination / "sentinel.txt",
    )


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
