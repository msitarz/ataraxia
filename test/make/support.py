# SPDX-License-Identifier: Apache-2.0
"""Disposable real-Make arrangements with a recording external uv boundary."""

from collections.abc import Mapping
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class UvCall:
    """Arguments and environment observed by the fixture executable."""

    argv: tuple[str, ...]
    environment: dict[str, str | None]


def read_calls(log: Path) -> tuple[UvCall, ...]:
    """Validate external log records before exposing typed observations."""
    calls: list[UvCall] = []
    for line in log.read_text().splitlines() if log.exists() else ():
        record: object = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError("uv record must be a mapping")
        arguments: object = record.get("argv")
        environment: object = record.get("environment")
        if not isinstance(arguments, list) or not isinstance(environment, dict):
            raise ValueError("uv record must contain arguments and environment")
        argv: list[str] = []
        observed: dict[str, str | None] = {}
        for argument in arguments:
            if not isinstance(argument, str):
                raise ValueError("uv argument must be a string")
            argv.append(argument)
        for name, value in environment.items():
            if not isinstance(name, str) or not (
                value is None or isinstance(value, str)
            ):
                raise ValueError("uv environment must contain string names and values")
            observed[name] = value
        calls.append(UvCall(tuple(argv), observed))
    return tuple(calls)


@dataclass(frozen=True)
class MakeResult:
    """Public process observations and recording-executable calls."""

    exit_code: int
    stdout: str
    stderr: str
    calls: tuple[UvCall, ...]

    @property
    def output(self) -> str:
        """Combine diagnostics for assertion failures."""
        return self.stdout + self.stderr


@dataclass(frozen=True)
class MakeSandbox:
    """Explicit isolated child environment and disposable Makefile directory."""

    directory: Path
    environment: dict[str, str]

    def run(
        self,
        *arguments: str,
        fail_args: tuple[str, ...] = (),
        exit_code: int = 1,
        stdout: str = "",
        stderr: str = "",
        timeout: float = 30,
        environment: Mapping[str, str] | None = None,
    ) -> MakeResult:
        """Run actual Make; optional exact uv arguments select a failed call."""
        log = self.directory / "uv-calls.jsonl"
        log.unlink(missing_ok=True)
        child = self.environment | dict(environment or {})
        child.update(
            STUB_UV_LOG=str(log),
            STUB_UV_FAIL_ARGS=json.dumps(fail_args),
            STUB_UV_EXIT=str(exit_code),
            STUB_UV_STDOUT=stdout,
            STUB_UV_STDERR=stderr,
        )
        process = subprocess.run(
            ["make", *arguments],
            cwd=self.directory,
            env=child,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return MakeResult(
            process.returncode, process.stdout, process.stderr, read_calls(log)
        )


def make_sandbox(directory: Path) -> MakeSandbox:
    """Copy only Make and expectation filenames required for stub routing."""
    directory.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "Makefile", directory / "Makefile")
    expectations = directory / "test/ataraxia/typecheck"
    expectations.mkdir(parents=True)
    for source in (ROOT / "test/ataraxia/typecheck").glob("*.py"):
        (expectations / source.name).touch()
    binary = directory / "bin"
    binary.mkdir()
    recorder = binary / "uv"
    shutil.copyfile(ROOT / "test/make/fixtures/uv_recorder.py", recorder)
    recorder.chmod(0o755)
    # Keep process-owned caches outside the repository's complete file snapshot.
    process = Path(
        tempfile.mkdtemp(prefix=f"{directory.name}-process-", dir=directory.parent)
    )
    home, scratch = process / "home", process / "tmp"
    home.mkdir()
    scratch.mkdir()
    return MakeSandbox(
        directory,
        {
            "PATH": f"{binary}:{Path(sys.executable).parent}:/usr/bin:/bin",
            "HOME": str(home),
            "TMPDIR": str(scratch),
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
        },
    )
