# SPDX-License-Identifier: Apache-2.0
"""Exercise Codex executable lookup and version probing across a process boundary."""

import os
from pathlib import Path

import pytest

from script.eval.model import DirectoryOption, HarnessConfig
from script.eval.runner.adapters import CodexCliBindingResolver


def configuration() -> HarnessConfig:
    """Create a minimal valid execution configuration for binding resolution."""
    return HarnessConfig.model_validate({
        "ordered_options": (DirectoryOption(position=0, path=Path("context")),),
        "models": ("gpt-6-luna",),
        "efforts": ("none",),
        "concurrency": 1,
        "output_directory": Path("out"),
        "dry_run": False,
        "timeout_seconds": 2.0,
        "cleanup_timeout_seconds": 2.0,
        "grace_seconds": 0.0,
        "output_limit_bytes": 4096,
        "instructions_file_path": None,
    })


def test_binding_resolves_path_and_probes_that_fake_executable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    executable = tmp_path / "codex"
    executable.write_text(
        "#!/bin/sh\nprintf '%s\\n' 'codex-cli 9.8.7'\n", encoding="utf-8"
    )
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    resolver = CodexCliBindingResolver(runner_version=lambda: "0.1.0")

    # When
    binding = resolver.resolve(configuration())

    # Then
    assert binding.executable_path == executable.resolve()
    assert binding.cli_version == "codex-cli 9.8.7"
    assert binding.runner_version == "0.1.0"
    assert binding.quota_scope is None


def test_binding_keeps_version_unknown_when_fake_probe_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    executable = tmp_path / "codex"
    executable.write_text("#!/bin/sh\nexit 17\n", encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", os.fspath(tmp_path))
    resolver = CodexCliBindingResolver(runner_version=lambda: "0.1.0")

    # When
    binding = resolver.resolve(configuration())

    # Then
    assert binding.executable_path == executable.resolve()
    assert binding.cli_version is None
    assert binding.quota_scope is None


def test_binding_reports_missing_codex_on_empty_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    empty_path = tmp_path / "empty"
    empty_path.mkdir()
    monkeypatch.setenv("PATH", os.fspath(empty_path))
    resolver = CodexCliBindingResolver(runner_version=lambda: "0.1.0")

    # When
    with pytest.raises(FileNotFoundError) as raised:
        resolver.resolve(configuration())

    # Then
    assert str(raised.value) == "Codex CLI executable was not found on PATH"
