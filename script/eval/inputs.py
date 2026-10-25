# SPDX-License-Identifier: Apache-2.0
"""Freeze tracked evaluation inputs against one clean Git commit."""

from hashlib import sha256
import math
import os
from pathlib import Path
import subprocess
from typing import Protocol

from script.eval.model import (
    DirectoryOption,
    FrozenInputs,
    HarnessConfig,
    InstructionsSnapshot,
    SourceSnapshot,
)


class RepositoryReader(Protocol):
    """Read-only Git and source boundary for frozen harness inputs."""

    def freeze(self, config: HarnessConfig, /) -> FrozenInputs:
        """Validate repository inputs and return commit-checked snapshots."""


class GitRepositoryReader:
    """Read source bytes and verify their identity against one Git HEAD."""

    def __init__(self, *, timeout_seconds: float = 30.0) -> None:
        if (
            isinstance(timeout_seconds, bool)
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise ValueError("Git timeout must be finite and positive")
        self._timeout_seconds = timeout_seconds

    def freeze(self, config: HarnessConfig, /) -> FrozenInputs:
        """Freeze immediate files from ordered directories and optional instructions.

        Returns:
            The one-commit snapshot of all selected inputs.

        """
        directories = tuple(
            option
            for option in config.ordered_options
            if isinstance(option, DirectoryOption)
        )
        input_paths = tuple(option.path for option in directories) + (
            (config.instructions_file_path,)
            if config.instructions_file_path is not None
            else ()
        )

        root, head = self._resolve_clean_repository(input_paths)
        relative_directories = tuple(
            self._safe_relative_path(root, option.path, directory=True)
            for option in directories
        )
        instruction_relative = (
            self._safe_relative_path(
                root, config.instructions_file_path, directory=False
            )
            if config.instructions_file_path is not None
            else None
        )

        discovered = self._discover_files(root, directories, relative_directories)
        instruction_path = root / instruction_relative if instruction_relative else None
        if instruction_path is not None:
            self._require_regular_file(instruction_path)
        tracked = self._tracked_paths(root, relative_directories, instruction_relative)
        self._require_tracked(
            discovered, instruction_relative, instruction_path, tracked
        )
        selected = tuple(relative for _, relative, _ in discovered) + (
            (instruction_relative,) if instruction_relative is not None else ()
        )
        blobs = self._commit_blobs(root, head, selected)
        sources = self._source_snapshots(discovered, blobs, head)
        instructions = self._instruction_snapshot(
            instruction_relative, instruction_path, blobs, head
        )
        return FrozenInputs(root, head, sources, instructions)

    def _resolve_clean_repository(self, paths: tuple[Path, ...]) -> tuple[Path, str]:
        roots = tuple(self._repository_root(path) for path in paths)
        root = roots[0]
        if any(candidate != root for candidate in roots[1:]):
            raise ValueError("all inputs must belong to the same Git repository")
        try:
            head_output = self._git(root, "rev-parse", "--verify", "HEAD^{commit}")
            head = head_output.decode().strip()
        except ValueError as exc:
            if str(exc).startswith("Git rev-parse failed"):
                raise ValueError(f"Git repository has no HEAD: {root}") from exc
            raise
        if not head:
            raise ValueError(f"Git repository has no HEAD: {root}")
        self._require_clean_checkout(root)
        return root, head

    def _discover_files(
        self,
        root: Path,
        directories: tuple[DirectoryOption, ...],
        relative_directories: tuple[str, ...],
    ) -> list[tuple[int, str, Path]]:
        discovered: list[tuple[int, str, Path]] = []
        for option, relative in zip(directories, relative_directories, strict=True):
            absolute = root / relative
            entries = self._directory_entries(absolute)
            file_count = 0
            for entry in entries:
                entry_path = Path(entry.path)
                if not self._is_selected_file(entry, entry_path):
                    continue
                relative_file = (Path(relative) / entry.name).as_posix()
                discovered.append((option.position, relative_file, entry_path))
                file_count += 1
            if not file_count:
                raise ValueError(
                    f"context directory has no immediate files: {absolute}"
                )
        return discovered

    @staticmethod
    def _directory_entries(absolute: Path) -> list[os.DirEntry[str]]:
        try:
            with os.scandir(absolute) as scan:
                entries = sorted(scan, key=lambda entry: entry.name)
        except OSError as exc:
            raise ValueError(
                f"cannot read context directory {absolute}: {exc}"
            ) from exc
        if not entries:
            raise ValueError(f"context directory is empty: {absolute}")
        return entries

    @staticmethod
    def _is_selected_file(entry: os.DirEntry[str], path: Path) -> bool:
        if entry.is_symlink():
            raise ValueError(f"symbolic-link input is not allowed: {path}")
        if entry.is_dir(follow_symlinks=False):
            if (path / ".git").exists():
                raise ValueError(f"nested Git repository or submodule input: {path}")
            return False
        if not entry.is_file(follow_symlinks=False):
            raise ValueError(f"context entries must be regular files: {path}")
        return True

    @staticmethod
    def _require_tracked(
        discovered: list[tuple[int, str, Path]],
        instruction_relative: str | None,
        instruction_path: Path | None,
        tracked: set[str],
    ) -> None:
        for _, relative, absolute in discovered:
            if relative not in tracked:
                raise ValueError(
                    f"input is not tracked at HEAD (or is ignored): {absolute}"
                )
        if instruction_relative is not None and instruction_relative not in tracked:
            raise ValueError(
                "instructions file is not tracked at HEAD (or is ignored): "
                f"{instruction_path}"
            )

    def _source_snapshots(
        self,
        discovered: list[tuple[int, str, Path]],
        blobs: dict[str, tuple[str, bytes]],
        head: str,
    ) -> tuple[SourceSnapshot, ...]:
        snapshots = []
        for position, relative, absolute in discovered:
            content = self._read_utf8(absolute)
            blob_sha, blob_content = blobs[relative]
            if content != blob_content:
                raise ValueError(f"input bytes differ from commit {head}: {absolute}")
            snapshots.append(
                SourceSnapshot(
                    directory_position=position,
                    repository_path=relative,
                    commit_blob_sha=blob_sha,
                    content_sha256=sha256(content).hexdigest(),
                    content=content,
                )
            )
        return tuple(snapshots)

    def _instruction_snapshot(
        self,
        relative: str | None,
        path: Path | None,
        blobs: dict[str, tuple[str, bytes]],
        head: str,
    ) -> InstructionsSnapshot | None:
        if relative is None or path is None:
            return None
        content = self._read_utf8(path)
        blob_sha, blob_content = blobs[relative]
        if content != blob_content:
            raise ValueError(
                f"instructions file bytes differ from commit {head}: {path}"
            )
        return InstructionsSnapshot(
            repository_path=relative,
            commit_blob_sha=blob_sha,
            content_sha256=sha256(content).hexdigest(),
            content=content,
        )

    def _repository_root(self, path: Path) -> Path:
        absolute = path if path.is_absolute() else Path.cwd() / path
        self._reject_symlink_components(absolute)
        probe = absolute if absolute.is_dir() else absolute.parent
        root_output = self._git(probe, "rev-parse", "--show-toplevel")
        if root_output.endswith(b"\n"):
            root_output = root_output[:-1]
        root = os.fsdecode(root_output)
        if not root:
            raise ValueError(f"input is not inside a Git worktree: {path}")
        canonical_root = Path(root).resolve(strict=True)
        if (canonical_root / ".git").is_file() or (canonical_root / ".git").is_dir():
            self._reject_nested_repository(canonical_root)
            return canonical_root
        raise ValueError(f"input is not inside a Git worktree: {path}")

    @staticmethod
    def _reject_nested_repository(root: Path) -> None:
        for ancestor in root.parents:
            git_marker = ancestor / ".git"
            if git_marker.is_file() or git_marker.is_dir():
                raise ValueError(
                    f"nested Git repository or submodule input is not allowed: {root}"
                )

    def _safe_relative_path(self, root: Path, path: Path, *, directory: bool) -> str:
        absolute = path if path.is_absolute() else Path.cwd() / path
        self._reject_symlink_components(absolute)
        try:
            resolved = absolute.resolve(strict=True)
            relative = resolved.relative_to(root)
        except (OSError, ValueError) as exc:
            raise ValueError(
                f"input must exist inside repository {root}: {path}"
            ) from exc
        if directory and not resolved.is_dir():
            raise ValueError(f"context input is not a directory: {path}")
        if not directory and not resolved.is_file():
            raise ValueError(f"instructions input is not a regular file: {path}")
        return relative.as_posix()

    @staticmethod
    def _reject_symlink_components(path: Path) -> None:
        absolute = path if path.is_absolute() else Path.cwd() / path
        current = Path(absolute.anchor)
        for component in absolute.parts[1:]:
            if component == "..":
                current = current.parent
                continue
            current /= component
            try:
                if current.is_symlink():
                    raise ValueError(
                        f"symbolic-link path component is not allowed: {current}"
                    )
            except OSError as exc:
                raise ValueError(f"cannot inspect input path {current}: {exc}") from exc

    @staticmethod
    def _require_regular_file(path: Path) -> None:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"instructions input is not a regular file: {path}")

    def _require_clean_checkout(self, root: Path) -> None:
        status = self._git(
            root, "status", "--porcelain=v1", "-z", "--untracked-files=all"
        )
        if status:
            raise ValueError(
                f"Git worktree must be clean, including untracked files: {root}"
            )

    def _tracked_paths(
        self, root: Path, directories: tuple[str, ...], instruction: str | None
    ) -> set[str]:
        pathspecs = tuple(
            ":(top)" if path == "." else f":(top,literal){path.rstrip('/')}/"
            for path in dict.fromkeys(directories)
        )
        if instruction is not None:
            pathspecs += (f":(top,literal){instruction}",)
        if not pathspecs:
            return set()
        output = self._git(
            root, "ls-files", "--cached", "--full-name", "-z", "--", *pathspecs
        )
        return {os.fsdecode(path) for path in output.split(b"\0") if path}

    def _commit_blobs(
        self, root: Path, commit: str, paths: tuple[str, ...]
    ) -> dict[str, tuple[str, bytes]]:
        unique_paths = tuple(dict.fromkeys(paths))
        pathspecs = tuple(f":(literal){path}" for path in unique_paths)
        output = self._git(
            root, "ls-tree", "-r", "-z", "--full-tree", commit, "--", *pathspecs
        )
        object_ids = self._blob_object_ids(output, unique_paths, commit)
        batch_input = ("\n".join(object_ids.values()) + "\n").encode()
        batch = self._git(root, "cat-file", "--batch", input_bytes=batch_input)
        return self._parse_blob_batch(batch, object_ids)

    @staticmethod
    def _blob_object_ids(
        output: bytes, paths: tuple[str, ...], commit: str
    ) -> dict[str, str]:
        object_ids: dict[str, str] = {}
        for record in output.split(b"\0"):
            if not record:
                continue
            metadata, raw_path = record.split(b"\t", 1)
            mode, kind, object_id = metadata.decode("ascii").split()
            path = os.fsdecode(raw_path)
            if path in paths:
                if kind != "blob" or mode == "120000":
                    raise ValueError(
                        f"input is not a regular tracked file at HEAD: {path}"
                    )
                object_ids[path] = object_id
        missing = set(paths) - object_ids.keys()
        if missing:
            raise ValueError(
                f"input is not present in commit {commit}: {sorted(missing)[0]}"
            )
        return object_ids

    @staticmethod
    def _parse_blob_batch(
        batch: bytes, object_ids: dict[str, str]
    ) -> dict[str, tuple[str, bytes]]:
        blobs: dict[str, tuple[str, bytes]] = {}
        cursor = 0
        for path, object_id in object_ids.items():
            line_end = batch.index(b"\n", cursor)
            header = batch[cursor:line_end].decode("ascii").split()
            if len(header) != 3 or header[0] != object_id or header[1] != "blob":
                raise ValueError(f"Git returned an invalid blob record for {path}")
            size = int(header[2])
            start, end = line_end + 1, line_end + 1 + size
            content = batch[start:end]
            if len(content) != size or batch[end : end + 1] != b"\n":
                raise ValueError(f"Git returned a truncated blob for {path}")
            blobs[path] = (object_id, content)
            cursor = end + 1
        return blobs

    def _read_utf8(self, path: Path) -> bytes:
        try:
            content = path.read_bytes()
            content.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise ValueError(f"input is not valid UTF-8: {path}") from exc
        except OSError as exc:
            raise ValueError(f"cannot read input {path}: {exc}") from exc
        return content

    def _git(self, cwd: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
        environment = os.environ.copy()
        environment["GIT_OPTIONAL_LOCKS"] = "0"
        for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
            environment.pop(name, None)
        try:
            result = subprocess.run(
                ["git", "-C", os.fspath(cwd), *args],
                input=input_bytes,
                capture_output=True,
                check=False,
                timeout=self._timeout_seconds,
                env=environment,
            )
        except subprocess.TimeoutExpired as exc:
            raise ValueError(
                f"Git command timed out after {self._timeout_seconds:g}s: {args[0]}"
            ) from exc
        except OSError as exc:
            raise ValueError(f"cannot run Git command {args[0]}: {exc}") from exc
        if result.returncode:
            diagnostic = result.stderr.decode("utf-8", errors="replace").strip()
            raise ValueError(
                f"Git {args[0]} failed in {cwd}: {diagnostic or result.returncode}"
            )
        return result.stdout
