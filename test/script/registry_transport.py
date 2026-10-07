# SPDX-License-Identifier: Apache-2.0
"""Script-owned transport arrangements narrowly reused by Make tests."""

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Literal

import pytest

ROOT = Path(__file__).resolve().parents[2]
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
    shutil.copyfile(ROOT / "test/script/fixtures/registry_uv.py", directory / "uv")
    (directory / "uv").chmod(0o755)


def registry_case(directory: Path, mode: Literal["record", "delegate"]) -> RegistryCase:
    """Prepare explicit process inputs without inheriting caller flags.

    Returns:
        A literal-argument or missing-input case.
    """
    process_directory = directory.parent / f"{directory.name}-process"
    home = process_directory / "home"
    temporary = process_directory / "tmp"
    home.mkdir(parents=True)
    temporary.mkdir()
    environment = {
        "PATH": f"{directory}:{Path(sys.executable).parent}:/usr/bin:/bin",
        "HOME": str(home),
        "TMPDIR": str(temporary),
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
    if not isinstance(value, list):
        raise ValueError("external uv log must contain string arguments")
    arguments: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError("external uv log must contain string arguments")
        arguments.append(item)
    argv = tuple(arguments)
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


@pytest.fixture
def registry_project(tmp_path: Path) -> Path:
    """Copy the unchanged actual production boundary into tmp_path."""
    project = tmp_path / "project"
    project.mkdir()
    copy_registry_project(project)
    return project


@pytest.fixture
def registry_literal_case(registry_project: Path) -> RegistryCase:
    """Arrange literal inputs for the external uv delegation boundary."""
    return registry_case(registry_project, "record")


@pytest.fixture
def registry_missing_case(registry_project: Path) -> RegistryCase:
    """Arrange omitted inputs for the actual repository CLI."""
    return registry_case(registry_project, "delegate")
