# SPDX-License-Identifier: Apache-2.0
"""Record host-reviewed cleanup authority bound to current sandbox material."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Literal, TypedDict, TypeGuard, cast

from script import sandbox, sandbox_execution


class DecisionRecord(TypedDict):
    """Reviewed handling for one complete material category."""

    action: Literal["retain", "discard"]
    reference: str
    destination: str | None


class MaterialSnapshot(TypedDict):
    """Current owned identity, preparation, workspace and output revision."""

    generation: str
    destination_device: int
    destination_inode: int
    owned_digest: str
    preparation_state: Literal["ready", "failed"]
    workspace_head: str | None
    workspace_digest: str
    outputs_digest: str
    execution_digest: str


class DispositionRecord(TypedDict):
    """Persisted approval and exact material it reviewed."""

    owner_id: str
    reviewer_id: str
    review_reference: str
    material: MaterialSnapshot
    workspace: DecisionRecord
    outputs: DecisionRecord
    diagnostics_reference: str | None


DECISION_FIELDS = DecisionRecord.__required_keys__ | DecisionRecord.__optional_keys__
MATERIAL_FIELDS = (
    MaterialSnapshot.__required_keys__ | MaterialSnapshot.__optional_keys__
)
DISPOSITION_FIELDS = (
    DispositionRecord.__required_keys__ | DispositionRecord.__optional_keys__
)
MAX_REFERENCE_LENGTH = 2048


@dataclass(frozen=True)
class MaterialDecision:
    """Trusted host decision to retain material or record reviewed discard."""

    action: Literal["retain", "discard"]
    reference: str
    destination: Path | None = None


@dataclass(frozen=True)
class ReviewedDisposition:
    """Host-supplied review and preservation decisions for current material."""

    reviewer_id: str
    review_reference: str
    workspace: MaterialDecision
    outputs: MaterialDecision
    diagnostics_reference: str | None = None


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _file_digest(parent: int, name: str, info: os.stat_result, path: Path) -> str:
    descriptor = os.open(
        name,
        os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0),
        dir_fd=parent,
    )
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
        ) != (info.st_dev, info.st_ino):
            raise ValueError(f"material file was replaced: {path}")
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
        after = os.fstat(descriptor)
        if (after.st_size, after.st_mtime_ns) != (opened.st_size, opened.st_mtime_ns):
            raise ValueError(f"material file changed while reading: {path}")
        return digest.hexdigest()
    finally:
        os.close(descriptor)


def _tree_entry(
    parent: int, name: str, relative: Path, path: Path
) -> tuple[tuple[str, str, int, str], int | None]:
    info = os.stat(name, dir_fd=parent, follow_symlinks=False)
    mode = stat.S_IMODE(info.st_mode)
    entry_name = relative.as_posix()
    if stat.S_ISDIR(info.st_mode):
        descriptor = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent,
        )
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            os.close(descriptor)
            raise ValueError(f"material directory was replaced: {path}")
        return (entry_name, "directory", mode, ""), descriptor
    if stat.S_ISREG(info.st_mode):
        return (entry_name, "file", mode, _file_digest(parent, name, info, path)), None
    if stat.S_ISLNK(info.st_mode):
        target = os.readlink(name, dir_fd=parent)
        return (entry_name, "symlink", mode, target), None
    raise ValueError(f"unsupported material entry: {path}")


def _open_tree_root(path: Path) -> int | None:
    if not path.is_absolute():
        raise ValueError("material path must be absolute")
    descriptor = os.open(
        path.anchor,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
    )
    try:
        for part in path.parts[1:]:
            try:
                before = os.stat(part, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                os.close(descriptor)
                return None
            if not stat.S_ISDIR(before.st_mode):
                raise ValueError(f"material path contains a non-directory: {path}")
            child = os.open(
                part,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=descriptor,
            )
            after = os.fstat(child)
            if (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino):
                os.close(child)
                raise ValueError(f"material path changed while opening: {path}")
            os.close(descriptor)
            descriptor = child
        return descriptor
    except Exception:
        with suppress(OSError):
            os.close(descriptor)
        raise


def _scan_tree(
    descriptor: int,
    path: Path,
    relative: Path,
    entries: list[tuple[str, str, int, str]],
) -> None:
    with os.scandir(descriptor) as iterator:
        children = sorted(iterator, key=lambda item: item.name)
    for child in children:
        child_path = path / relative / child.name
        child_relative = relative / child.name
        entry, child_descriptor = _tree_entry(
            descriptor, child.name, child_relative, child_path
        )
        entries.append(entry)
        if child_descriptor is not None:
            try:
                _scan_tree(child_descriptor, path, child_relative, entries)
            finally:
                os.close(child_descriptor)


def _tree(path: Path) -> tuple[str, bool]:
    """Hash a tree without following symlinks.

    Returns:
        The material digest and whether the root exists.
    """
    descriptor = _open_tree_root(path)
    if descriptor is None:
        return _digest(["missing"]), False
    try:
        entries: list[tuple[str, str, int, str]] = []
        _scan_tree(descriptor, path, Path(), entries)
        return _digest(entries), True
    finally:
        os.close(descriptor)


def _git_head(workspace: Path) -> str | None:
    try:
        head = sandbox.run([
            "git",
            "-C",
            str(workspace),
            "rev-parse",
            "--verify",
            "HEAD",
        ])
    except sandbox.CommandFailure:
        return None
    if re.fullmatch(r"[0-9a-f]{40,64}", head) is None:
        raise ValueError("workspace returned a malformed Git tip")
    return head


def _current_material(scope: sandbox.SandboxScope) -> MaterialSnapshot:
    if scope.record is None or scope.generation is None:
        raise ValueError("cleanup disposition requires a reserved sandbox")
    state = sandbox_execution.read_execution_state(scope)
    if scope.record is None:
        raise ValueError("cleanup disposition requires a reserved sandbox")
    if scope.record.owned["state"] == "preparing":
        raise ValueError("sandbox preparation must finish or fail before disposition")
    preparation_state = scope.record.owned["state"]
    if state is not None and any(
        attempt["status"] in ("running", "unknown") for attempt in state["attempts"]
    ):
        raise ValueError("unknown or running execution cannot be approved")
    workspace = scope.root / scope.name
    workspace_digest, workspace_present = _tree(workspace)
    head = _git_head(workspace) if workspace_present else None
    if scope.record.owned["state"] == "ready" and head is None:
        raise ValueError("ready sandbox has no current Git tip")
    outputs = scope.root / f".{scope.name}.runs"
    output_digest = _output_digest(outputs, state)
    owned = scope.record.owned
    execution_digest = _digest(state)
    return {
        "generation": scope.generation,
        "destination_device": owned["destination_device"],
        "destination_inode": owned["destination_inode"],
        "owned_digest": _digest(owned),
        "preparation_state": preparation_state,
        "workspace_head": head,
        "workspace_digest": workspace_digest,
        "outputs_digest": output_digest,
        "execution_digest": execution_digest,
    }


def _output_digest(
    output_root: Path, state: sandbox_execution.ExecutionState | None
) -> str:
    descriptor = _open_tree_root(output_root)
    if descriptor is None:
        return _digest(["missing"])
    try:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o700
        ):
            raise ValueError("private execution output root is unsafe")
        expected: dict[str, str] = {}
        if state is not None:
            expected = {
                item["run_id"]: item["artifact_dir"]
                for item in state["attempts"]
                if item["artifact_dir"]
            }
        with os.scandir(descriptor) as iterator:
            children = sorted(iterator, key=lambda item: item.name)
        if {child.name for child in children} != set(expected):
            raise ValueError("private outputs do not match recorded attempts")
        for child in children:
            child_info = os.stat(child.name, dir_fd=descriptor, follow_symlinks=False)
            if (
                not stat.S_ISDIR(child_info.st_mode)
                or child_info.st_uid != os.getuid()
                or stat.S_IMODE(child_info.st_mode) != 0o700
                or expected[child.name] != str(output_root / child.name)
            ):
                raise ValueError("private execution artifact directory is unsafe")
        entries: list[tuple[str, str, int, str]] = []
        _scan_tree(descriptor, output_root, Path(), entries)
        return _digest(entries)
    finally:
        os.close(descriptor)


def _safe_destination(scope: sandbox.SandboxScope, destination: Path) -> None:
    if (
        not destination.is_absolute()
        or destination != Path(os.path.abspath(destination))
        or destination == scope.root
        or destination in scope.root.parents
        or scope.root in destination.parents
    ):
        raise ValueError("retention destination cannot overlap the managed root")
    cursor = Path(destination.anchor)
    try:
        for part in destination.parts[1:]:
            cursor /= part
            info = cursor.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise ValueError("retention destination cannot traverse symlinks")
    except FileNotFoundError as error:
        raise ValueError("retention destination does not exist") from error


def _decision(
    decision: MaterialDecision,
    *,
    material_path: Path,
    material_digest: str,
    material_present: bool,
    scope: sandbox.SandboxScope,
) -> DecisionRecord:
    if not _is_bounded_text(decision.reference):
        raise ValueError("material decision requires a bounded review reference")
    if decision.action == "discard":
        if decision.destination is not None:
            raise ValueError("discard decision cannot name a retention destination")
        return {
            "action": "discard",
            "reference": decision.reference,
            "destination": None,
        }
    if (
        decision.action != "retain"
        or decision.destination is None
        or not material_present
    ):
        raise ValueError("retaining requires present material and a destination")
    destination = decision.destination
    _safe_destination(scope, destination)
    retained_digest, retained_present = _tree(destination)
    source_digest, source_present = _tree(material_path)
    if (
        not retained_present
        or not source_present
        or retained_digest != source_digest
        or source_digest != material_digest
    ):
        raise ValueError("retention destination does not match current material")
    return {
        "action": "retain",
        "reference": decision.reference,
        "destination": str(destination),
    }


def _is_bounded_text(value: object) -> TypeGuard[str]:
    return (
        isinstance(value, str)
        and bool(value)
        and len(value) <= MAX_REFERENCE_LENGTH
        and not any(ord(character) < 32 for character in value)
    )


def _is_hex(value: object, *, lengths: range | tuple[int, ...]) -> TypeGuard[str]:
    return (
        isinstance(value, str)
        and len(value) in lengths
        and all(character in "0123456789abcdef" for character in value)
    )


def _parse_decision(raw: object) -> DecisionRecord | None:
    if not isinstance(raw, dict) or set(raw) != DECISION_FIELDS:
        return None
    action = raw.get("action")
    reference = raw.get("reference")
    destination = raw.get("destination")
    if action not in ("retain", "discard") or not _is_bounded_text(reference):
        return None
    if action == "retain":
        if not isinstance(destination, str):
            return None
        return {"action": "retain", "reference": reference, "destination": destination}
    if destination is not None:
        return None
    return {"action": "discard", "reference": reference, "destination": None}


def _parse_material(raw: object) -> MaterialSnapshot | None:
    if not isinstance(raw, dict) or set(raw) != MATERIAL_FIELDS:
        return None
    generation = raw.get("generation")
    state = raw.get("preparation_state")
    owned_digest = raw.get("owned_digest")
    workspace_digest = raw.get("workspace_digest")
    outputs_digest = raw.get("outputs_digest")
    execution_digest = raw.get("execution_digest")
    device = raw.get("destination_device")
    inode = raw.get("destination_inode")
    head = raw.get("workspace_head")
    if (
        not _is_hex(generation, lengths=(32,))
        or state not in ("ready", "failed")
        or not _is_hex(owned_digest, lengths=(64,))
        or not _is_hex(workspace_digest, lengths=(64,))
        or not _is_hex(outputs_digest, lengths=(64,))
        or not _is_hex(execution_digest, lengths=(64,))
        or not isinstance(device, int)
        or isinstance(device, bool)
        or not isinstance(inode, int)
        or isinstance(inode, bool)
        or (head is not None and not _is_hex(head, lengths=range(40, 65)))
        or (state == "ready" and head is None)
    ):
        return None
    return {
        "generation": generation,
        "destination_device": device,
        "destination_inode": inode,
        "owned_digest": owned_digest,
        "preparation_state": state,
        "workspace_head": head,
        "workspace_digest": workspace_digest,
        "outputs_digest": outputs_digest,
        "execution_digest": execution_digest,
    }


def _parse_disposition(raw: object) -> DispositionRecord | None:
    if not isinstance(raw, dict) or set(raw) != DISPOSITION_FIELDS:
        return None
    owner_id = raw.get("owner_id")
    reviewer_id = raw.get("reviewer_id")
    review_reference = raw.get("review_reference")
    diagnostics = raw.get("diagnostics_reference")
    material = _parse_material(raw.get("material"))
    workspace = _parse_decision(raw.get("workspace"))
    outputs = _parse_decision(raw.get("outputs"))
    if not _is_bounded_text(owner_id):
        return None
    if not _is_bounded_text(reviewer_id):
        return None
    if not _is_bounded_text(review_reference):
        return None
    if material is None or workspace is None or outputs is None:
        return None
    if diagnostics is not None and not _is_bounded_text(diagnostics):
        return None
    return {
        "owner_id": owner_id,
        "reviewer_id": reviewer_id,
        "review_reference": review_reference,
        "material": material,
        "workspace": workspace,
        "outputs": outputs,
        "diagnostics_reference": diagnostics,
    }


def _validate_reviewed_input(
    scope: sandbox.SandboxScope, reviewed: ReviewedDisposition
) -> None:
    if not all(
        _is_bounded_text(value)
        for value in (reviewed.reviewer_id, reviewed.review_reference)
    ):
        raise ValueError("review identity and reference must be bounded plain text")
    if (
        scope.record is not None
        and scope.record.owned["state"] == "failed"
        and not reviewed.diagnostics_reference
    ):
        raise ValueError("failed preparation diagnostics require explicit review")


def record_disposition(
    scope: sandbox.SandboxScope,
    *,
    owner_id: str,
    source_repository: Path | None,
    work: str | None,
    reviewed: ReviewedDisposition,
) -> DispositionRecord:
    """Persist explicit trusted-host disposition for the exact current material.

    The caller is the trusted orchestration/review boundary. This method checks
    identity and preservation claims; it does not authenticate review references.

    Returns:
        The persisted disposition record.

    Raises:
        ValueError: If identity, review, material, or preservation checks fail.
    """
    if scope.record is None:
        raise ValueError("cleanup disposition requires a reserved sandbox")
    binding = sandbox_execution.work_binding(
        scope,
        owner_id=owner_id,
        source_repository=source_repository,
        work=work,
    )
    state = sandbox_execution.read_execution_state(scope)
    if state is None:
        state = sandbox_execution.ExecutionState(binding=binding, attempts=[])
        sandbox.update_marker(
            scope,
            {
                "execution": cast(sandbox.JsonValue, state),
                "cleanup_disposition": None,
            },
        )
        if scope.record is None:
            raise ValueError("failed to persist Work binding")
    current = _current_material(scope)
    workspace_path = scope.root / scope.name
    output_path = scope.root / f".{scope.name}.runs"
    workspace_digest, workspace_present = _tree(workspace_path)
    output_digest, output_present = _tree(output_path)
    workspace_decision = _decision(
        reviewed.workspace,
        material_path=workspace_path,
        material_digest=workspace_digest,
        material_present=workspace_present,
        scope=scope,
    )
    output_decision = _decision(
        reviewed.outputs,
        material_path=output_path,
        material_digest=output_digest,
        material_present=output_present,
        scope=scope,
    )
    _validate_reviewed_input(scope, reviewed)
    record: DispositionRecord = {
        "owner_id": binding["owner_id"],
        "reviewer_id": reviewed.reviewer_id,
        "review_reference": reviewed.review_reference,
        "material": current,
        "workspace": workspace_decision,
        "outputs": output_decision,
        "diagnostics_reference": reviewed.diagnostics_reference,
    }
    if _parse_disposition(record) is None:
        raise ValueError("cleanup disposition input is malformed")
    if _current_material(scope) != current:
        raise ValueError("sandbox material changed while disposition was reviewed")
    sandbox.update_marker(
        scope,
        {
            "execution": cast(sandbox.JsonValue, state),
            "cleanup_disposition": cast(sandbox.JsonValue, record),
        },
    )
    return record


def validate_disposition(
    scope: sandbox.SandboxScope, *, owner_id: str
) -> DispositionRecord:
    """Return current validated disposition or refuse stale/malformed data.

    Raises:
        ValueError: If the approval or any bound material is missing or stale.
    """
    if scope.record is None:
        raise ValueError("cleanup disposition requires a reserved sandbox")
    state = sandbox_execution.read_execution_state(scope)
    if state is None or state["binding"]["owner_id"] != owner_id:
        raise ValueError("cleanup disposition has no matching Work/owner binding")
    raw = scope.record.extensions.get("cleanup_disposition")
    record = _parse_disposition(raw)
    if record is None or record["owner_id"] != owner_id:
        raise ValueError("cleanup disposition is missing or malformed")
    current = _current_material(scope)
    if record["material"] != current:
        raise ValueError("cleanup disposition no longer matches current material")
    failed = scope.record.owned["state"] == "failed"
    if failed and not record["diagnostics_reference"]:
        raise ValueError("failed preparation diagnostics lack reviewed disposition")
    _validate_retained(scope, record["workspace"], scope.root / scope.name)
    _validate_retained(scope, record["outputs"], scope.root / f".{scope.name}.runs")
    return record


def _validate_retained(
    scope: sandbox.SandboxScope, decision: DecisionRecord, source: Path
) -> None:
    if decision["action"] == "discard":
        return
    destination = decision["destination"]
    if destination is None:
        raise ValueError("retention destination is missing")
    retained = Path(destination)
    _safe_destination(scope, retained)
    digest, present = _tree(source)
    destination_digest, destination_present = _tree(retained)
    if (
        not destination_present
        or not present
        or digest != destination_digest
        or retained.is_symlink()
    ):
        raise ValueError("retained material changed or became unsafe")
