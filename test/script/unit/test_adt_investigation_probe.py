# SPDX-License-Identifier: Apache-2.0
"""One-time complete-boundary probe for three sandbox record models."""

from collections.abc import Callable
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from typing import Literal, NotRequired, TypedDict

import pytest

type JsonValue = (
    str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None
)
type State = Literal["preparing", "ready", "failed"]
type Candidate = Literal["flat", "tagged", "dataclass"]
type DiagnosticKey = Literal[
    "failure_stage", "failure_status", "failure_stdout", "failure_stderr"
]

DIAGNOSTICS: tuple[DiagnosticKey, ...] = (
    "failure_stage",
    "failure_status",
    "failure_stdout",
    "failure_stderr",
)
COMMON_KEYS = (
    "schema_version",
    "generation",
    "common_dir",
    "project",
    "base",
    "destination_device",
    "destination_inode",
    "state",
)


class FlatRecord(TypedDict):
    """Seed-compatible flat owned record with optional diagnostics."""

    schema_version: int
    generation: str
    common_dir: str
    project: str
    base: str
    destination_device: int
    destination_inode: int
    state: State
    failure_stage: NotRequired[str]
    failure_status: NotRequired[str]
    failure_stdout: NotRequired[str]
    failure_stderr: NotRequired[str]


class PreparingRecord(TypedDict):
    """Tagged preparing record with shared marker product fields."""

    schema_version: int
    generation: str
    common_dir: str
    project: str
    base: str
    destination_device: int
    destination_inode: int
    state: Literal["preparing"]


class ReadyRecord(TypedDict):
    """Tagged ready record with shared marker product fields."""

    schema_version: int
    generation: str
    common_dir: str
    project: str
    base: str
    destination_device: int
    destination_inode: int
    state: Literal["ready"]


class FailedRecord(TypedDict):
    """Tagged failed record with required diagnostics."""

    schema_version: int
    generation: str
    common_dir: str
    project: str
    base: str
    destination_device: int
    destination_inode: int
    state: Literal["failed"]
    failure_stage: str
    failure_status: str
    failure_stdout: str
    failure_stderr: str


type TaggedRecord = PreparingRecord | ReadyRecord | FailedRecord


@dataclass(frozen=True)
class FailureDiagnostics:
    """Four diagnostic strings required by a failed lifecycle."""

    stage: str
    status: str
    stdout: str
    stderr: str


@dataclass(frozen=True)
class Preparing:
    """Preparing lifecycle alternative."""

    pass


@dataclass(frozen=True)
class Ready:
    """Ready lifecycle alternative."""

    pass


@dataclass(frozen=True)
class Failed:
    """Failed lifecycle alternative with diagnostics."""

    diagnostics: FailureDiagnostics


type Lifecycle = Preparing | Ready | Failed


@dataclass(frozen=True)
class Owner:
    """Shared source ownership fields."""

    common_dir: str
    project: str
    base: str


@dataclass(frozen=True)
class DestinationIdentity:
    """Captured destination device and inode."""

    device: int
    inode: int


@dataclass(frozen=True)
class DataclassRecord:
    """Complete dataclass product with a lifecycle sum and extensions."""

    schema_version: int
    generation: str
    owner: Owner
    destination: DestinationIdentity
    lifecycle: Lifecycle
    extensions: dict[str, JsonValue]

    def __post_init__(self) -> None:
        validate_product(
            self.schema_version,
            self.generation,
            self.owner,
            self.destination,
            self.lifecycle,
            self.extensions,
        )


@dataclass(frozen=True)
class ValidatedRecord:
    """Narrow, complete product produced only after external validation."""

    schema_version: int
    generation: str
    owner: Owner
    destination: DestinationIdentity
    lifecycle: Lifecycle
    extensions: dict[str, JsonValue]

    def __post_init__(self) -> None:
        validate_product(
            self.schema_version,
            self.generation,
            self.owner,
            self.destination,
            self.lifecycle,
            self.extensions,
        )


def validate_product(
    schema_version: int,
    generation: str,
    owner: Owner,
    destination: DestinationIdentity,
    lifecycle: Lifecycle,
    extensions: dict[str, JsonValue],
) -> None:
    """Enforce the complete domain contract at typed construction boundaries."""
    if isinstance(schema_version, bool) or schema_version != 1:
        raise ValueError("unsupported sandbox metadata")
    if not re.fullmatch(r"[0-9a-f]{32}", generation):
        raise ValueError("malformed sandbox generation")
    if not all(
        isinstance(value, str)
        for value in (owner.common_dir, owner.project, owner.base)
    ):
        raise ValueError("malformed sandbox ownership")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in (destination.device, destination.inode)
    ):
        raise ValueError("malformed sandbox destination identity")
    if isinstance(lifecycle, Failed):
        details = lifecycle.diagnostics
        if not all(
            isinstance(value, str)
            for value in (details.stage, details.status, details.stdout, details.stderr)
        ):
            raise ValueError("incomplete sandbox failure diagnostics")
    if not all(
        isinstance(key, str) and is_json_value(value)
        for key, value in extensions.items()
    ):
        raise ValueError("malformed sandbox metadata")


@dataclass(frozen=True)
class FlatMarker:
    """Flat record and separately owned extension data."""

    owned: FlatRecord
    extensions: dict[str, JsonValue]

    def __post_init__(self) -> None:
        parse_and_validate(serialize_marker(self), "marker.json")


@dataclass(frozen=True)
class TaggedMarker:
    """Tagged record and separately owned extension data."""

    owned: TaggedRecord
    extensions: dict[str, JsonValue]

    def __post_init__(self) -> None:
        parse_and_validate(serialize_marker(self), "marker.json")


type Marker = FlatMarker | TaggedMarker | DataclassRecord


def sample_record(state: State = "failed") -> dict[str, JsonValue]:
    """Build a complete valid pinned-seed record for one lifecycle state.

    Returns:
        A JSON-compatible full record.
    """
    record: dict[str, JsonValue] = {
        "schema_version": 1,
        "generation": "0123456789abcdef0123456789abcdef",
        "common_dir": "/repo/.git",
        "project": "ataraxia",
        "base": "a" * 40,
        "destination_device": 4,
        "destination_inode": 9,
        "state": state,
        "opaque_extension": {"future": ["preserved", 3.5]},
    }
    if state == "failed":
        record.update({
            "failure_stage": "setup",
            "failure_status": "1",
            "failure_stdout": "out",
            "failure_stderr": "err",
        })
    return record


def parse_and_validate(data: bytes, path: str) -> ValidatedRecord:
    """Decode and validate the complete record before candidate construction.

    Returns:
        A complete typed product and separately owned extensions.

    Raises:
        ValueError: If decoding or complete record validation fails.
    """
    try:
        raw: object = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"malformed sandbox metadata: {path}") from exc
    if not isinstance(raw, dict) or any(not isinstance(key, str) for key in raw):
        raise ValueError(f"malformed sandbox metadata: {path}")
    if not all(is_json_value(value) for value in raw.values()):
        raise ValueError(f"malformed sandbox metadata: {path}")
    _validate_consumed_fields(raw, path)
    owned_keys = set(COMMON_KEYS) | set(DIAGNOSTICS)
    extensions = {key: value for key, value in raw.items() if key not in owned_keys}
    schema_value = raw.get("schema_version")
    if not isinstance(schema_value, int) or isinstance(schema_value, bool):
        raise ValueError(f"unsupported sandbox metadata: {path}")
    generation = _required_string(
        raw, "generation", path, "malformed sandbox generation"
    )
    common_dir = _required_string(
        raw, "common_dir", path, "malformed sandbox ownership"
    )
    project = _required_string(raw, "project", path, "malformed sandbox ownership")
    base = _required_string(raw, "base", path, "malformed sandbox ownership")
    device = _required_nonnegative_int(raw, "destination_device", path)
    inode = _required_nonnegative_int(raw, "destination_inode", path)
    raw_state = raw.get("state")
    if raw_state == "preparing":
        state: State = "preparing"
    elif raw_state == "ready":
        state = "ready"
    elif raw_state == "failed":
        state = "failed"
    else:
        raise ValueError(f"malformed sandbox state: {path}")
    lifecycle = make_lifecycle(raw, state, path)
    return ValidatedRecord(
        schema_value,
        generation,
        Owner(common_dir, project, base),
        DestinationIdentity(device, inode),
        lifecycle,
        extensions,
    )


def _required_string(
    raw: dict[str, JsonValue], key: str, path: str, message: str
) -> str:
    value = raw.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{message}: {path}")
    return value


def _required_nonnegative_int(raw: dict[str, JsonValue], key: str, path: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"malformed sandbox destination identity: {path}")
    return value


def read_metadata_file(path: Path) -> bytes:
    """Read marker bytes and retain an I/O cause in the contextual error.

    Returns:
        The file's exact bytes.

    Raises:
        ValueError: If the read fails, with the original I/O error as its cause.
    """
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ValueError(f"malformed sandbox metadata: {path}") from exc


def _validate_consumed_fields(raw: dict[str, JsonValue], path: str) -> None:
    schema = raw.get("schema_version")
    if not isinstance(schema, int) or isinstance(schema, bool) or schema != 1:
        raise ValueError(f"unsupported sandbox metadata: {path}")
    generation = raw.get("generation")
    if not isinstance(generation, str) or not re.fullmatch(r"[0-9a-f]{32}", generation):
        raise ValueError(f"malformed sandbox generation: {path}")
    if any(
        not isinstance(raw.get(key), str) for key in ("common_dir", "project", "base")
    ):
        raise ValueError(f"malformed sandbox ownership: {path}")
    state = raw.get("state")
    if state not in ("preparing", "ready", "failed"):
        raise ValueError(f"malformed sandbox state: {path}")
    for key in DIAGNOSTICS:
        value = raw.get(key)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"malformed sandbox diagnostics: {path}")
    if state == "failed" and not all(
        isinstance(raw.get(key), str) for key in DIAGNOSTICS
    ):
        raise ValueError(f"incomplete sandbox failure diagnostics: {path}")
    if state != "failed" and any(key in raw for key in DIAGNOSTICS):
        raise ValueError(f"unexpected sandbox failure diagnostics: {path}")
    for key in ("destination_device", "destination_inode"):
        value = raw.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"malformed sandbox destination identity: {path}")


def is_json_value(value: object) -> bool:
    """Check the seed's recursive finite JSON value contract.

    Returns:
        Whether the value is a finite JSON-compatible value.
    """
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and is_json_value(item) for key, item in value.items()
        )
    return False


def construct_marker(candidate: Candidate, data: bytes) -> Marker:
    """Construct one representation after complete external validation.

    Returns:
        The selected complete marker representation.
    """
    parsed = parse_and_validate(data, "marker.json")
    if candidate == "flat":
        return FlatMarker(flat_record(parsed), parsed.extensions)
    if candidate == "tagged":
        return TaggedMarker(tagged_record(parsed), parsed.extensions)
    return DataclassRecord(
        parsed.schema_version,
        parsed.generation,
        parsed.owner,
        parsed.destination,
        parsed.lifecycle,
        parsed.extensions,
    )


def flat_record(parsed: ValidatedRecord) -> FlatRecord:
    result: FlatRecord = {
        "schema_version": parsed.schema_version,
        "generation": parsed.generation,
        "common_dir": parsed.owner.common_dir,
        "project": parsed.owner.project,
        "base": parsed.owner.base,
        "destination_device": parsed.destination.device,
        "destination_inode": parsed.destination.inode,
        "state": lifecycle_state(parsed.lifecycle),
    }
    if isinstance(parsed.lifecycle, Failed):
        details = parsed.lifecycle.diagnostics
        result.update({
            "failure_stage": details.stage,
            "failure_status": details.status,
            "failure_stdout": details.stdout,
            "failure_stderr": details.stderr,
        })
    return result


def tagged_record(parsed: ValidatedRecord) -> TaggedRecord:
    match parsed.lifecycle:
        case Preparing():
            return PreparingRecord(
                schema_version=parsed.schema_version,
                generation=parsed.generation,
                common_dir=parsed.owner.common_dir,
                project=parsed.owner.project,
                base=parsed.owner.base,
                destination_device=parsed.destination.device,
                destination_inode=parsed.destination.inode,
                state="preparing",
            )
        case Ready():
            return ReadyRecord(
                schema_version=parsed.schema_version,
                generation=parsed.generation,
                common_dir=parsed.owner.common_dir,
                project=parsed.owner.project,
                base=parsed.owner.base,
                destination_device=parsed.destination.device,
                destination_inode=parsed.destination.inode,
                state="ready",
            )
        case Failed(diagnostics=details):
            return FailedRecord(
                schema_version=parsed.schema_version,
                generation=parsed.generation,
                common_dir=parsed.owner.common_dir,
                project=parsed.owner.project,
                base=parsed.owner.base,
                destination_device=parsed.destination.device,
                destination_inode=parsed.destination.inode,
                state="failed",
                failure_stage=details.stage,
                failure_status=details.status,
                failure_stdout=details.stdout,
                failure_stderr=details.stderr,
            )


def lifecycle_state(lifecycle: Lifecycle) -> State:
    match lifecycle:
        case Preparing():
            return "preparing"
        case Ready():
            return "ready"
        case Failed():
            return "failed"


def make_lifecycle(owned: dict[str, JsonValue], state: State, path: str) -> Lifecycle:
    """Adapt validated flat fields to the dataclass lifecycle sum.

    Returns:
        The lifecycle alternative represented by the flat fields.
    """
    if state == "failed":
        return Failed(
            FailureDiagnostics(
                _diagnostic_string(owned, "failure_stage", path),
                _diagnostic_string(owned, "failure_status", path),
                _diagnostic_string(owned, "failure_stdout", path),
                _diagnostic_string(owned, "failure_stderr", path),
            )
        )
    if state == "ready":
        return Ready()
    return Preparing()


def _diagnostic_string(
    record: dict[str, JsonValue], key: DiagnosticKey, path: str
) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise ValueError(f"incomplete sandbox failure diagnostics: {path}")
    return value


def serialize_marker(marker: Marker) -> bytes:
    """Flatten one candidate and its extensions to JSON bytes.

    Returns:
        JSON bytes for the original persisted record shape.
    """
    if isinstance(marker, (FlatMarker, TaggedMarker)):
        raw = marker.extensions | marker.owned
    else:
        raw = {
            "schema_version": marker.schema_version,
            "generation": marker.generation,
            "common_dir": marker.owner.common_dir,
            "project": marker.owner.project,
            "base": marker.owner.base,
            "destination_device": marker.destination.device,
            "destination_inode": marker.destination.inode,
            **serialize_lifecycle(marker.lifecycle),
            **marker.extensions,
        }
    return (json.dumps(raw, sort_keys=True) + "\n").encode()


def serialize_lifecycle(lifecycle: Lifecycle) -> dict[str, JsonValue]:
    """Serialize lifecycle alternatives to the seed's state and diagnostic keys.

    Returns:
        The state and any required diagnostic fields.
    """
    match lifecycle:
        case Preparing():
            return {"state": "preparing"}
        case Ready():
            return {"state": "ready"}
        case Failed(diagnostics=details):
            return {
                "state": "failed",
                "failure_stage": details.stage,
                "failure_status": details.status,
                "failure_stdout": details.stdout,
                "failure_stderr": details.stderr,
            }


def failure_status(marker: Marker) -> str | None:
    """Return the status through the representation-specific pure decision."""
    if isinstance(marker, FlatMarker):
        if marker.owned["state"] == "failed":
            return marker.owned.get("failure_status")
        return None
    if isinstance(marker, TaggedMarker):
        if marker.owned["state"] == "failed":
            return marker.owned["failure_status"]
        return None
    match marker.lifecycle:
        case Failed(diagnostics=details):
            return details.status
        case Preparing() | Ready():
            return None


def transition_ready(marker: Marker) -> Marker:
    """Apply the pinned preparing-to-ready transition and revalidate the result.

    Returns:
        A complete updated marker preserving its extensions.

    Raises:
        ValueError: If the source marker is not in the preparing state.
    """
    parsed = parse_and_validate(serialize_marker(marker), "marker.json")
    if not isinstance(parsed.lifecycle, Preparing):
        raise ValueError("sandbox preparation state cannot be reassigned")
    updated = ValidatedRecord(
        parsed.schema_version,
        parsed.generation,
        parsed.owner,
        parsed.destination,
        Ready(),
        parsed.extensions.copy(),
    )
    if isinstance(marker, FlatMarker):
        return FlatMarker(flat_record(updated), updated.extensions)
    if isinstance(marker, TaggedMarker):
        return TaggedMarker(tagged_record(updated), updated.extensions)
    return DataclassRecord(
        updated.schema_version,
        updated.generation,
        updated.owner,
        updated.destination,
        updated.lifecycle,
        updated.extensions,
    )


def _remove_inode(record: dict[str, JsonValue]) -> None:
    del record["destination_inode"]


def _wrong_project_type(record: dict[str, JsonValue]) -> None:
    record["project"] = 3


def _boolean_schema(record: dict[str, JsonValue]) -> None:
    record["schema_version"] = True


def _boolean_device(record: dict[str, JsonValue]) -> None:
    record["destination_device"] = False


def _negative_inode(record: dict[str, JsonValue]) -> None:
    record["destination_inode"] = -1


def _null_failed_diagnostic(record: dict[str, JsonValue]) -> None:
    record["failure_stderr"] = None


def _null_ready_diagnostic(record: dict[str, JsonValue]) -> None:
    record["failure_stage"] = None


def _nonfinite_extension(record: dict[str, JsonValue]) -> None:
    record["opaque_extension"] = float("nan")


def matches_int_pattern(value: object) -> bool:
    """Probe Python's runtime behavior for an ``int()`` class pattern.

    Returns:
        Whether the value matches an ``int()`` class pattern.
    """
    match value:
        case int():
            return True
        case _:
            return False


@pytest.mark.parametrize(
    "candidate",
    ["flat", "tagged", "dataclass"],
    ids=["flat-record", "tagged-record", "dataclass-union"],
)
def test_each_candidate_roundtrips_complete_record_and_updates_state(
    candidate: Candidate,
) -> None:
    """Each candidate roundtrips the complete record and its valid update."""
    # Given
    raw = sample_record()
    encoded = json.dumps(raw).encode()

    # When
    marker = construct_marker(candidate, encoded)
    roundtrip = json.loads(serialize_marker(marker))
    preparing = construct_marker(
        candidate, json.dumps(sample_record("preparing")).encode()
    )
    updated = transition_ready(preparing)
    updated_raw = json.loads(serialize_marker(updated))

    # Then
    assert failure_status(marker) == "1"
    assert roundtrip == raw
    assert updated_raw["state"] == "ready"
    assert all(key not in updated_raw for key in DIAGNOSTICS)
    assert updated_raw["opaque_extension"] == raw["opaque_extension"]


@pytest.mark.parametrize(
    "candidate",
    ["flat", "tagged", "dataclass"],
    ids=["flat-record", "tagged-record", "dataclass-union"],
)
@pytest.mark.parametrize(
    ("state", "change", "message"),
    [
        ("ready", _remove_inode, "malformed sandbox destination identity"),
        ("ready", _wrong_project_type, "malformed sandbox ownership"),
        ("ready", _boolean_schema, "unsupported sandbox metadata"),
        ("ready", _boolean_device, "malformed sandbox destination identity"),
        ("ready", _negative_inode, "malformed sandbox destination identity"),
        ("failed", _null_failed_diagnostic, "incomplete sandbox failure diagnostics"),
        ("ready", _null_ready_diagnostic, "unexpected sandbox failure diagnostics"),
        ("ready", _nonfinite_extension, "malformed sandbox metadata"),
    ],
    ids=[
        "missing-identity",
        "wrong-owner-type",
        "bool-schema",
        "bool-device",
        "negative-inode",
        "failed-null",
        "ready-null-key",
        "nonfinite-extension",
    ],
)
def test_each_candidate_rejects_invalid_complete_record(
    candidate: Candidate,
    state: State,
    change: Callable[[dict[str, JsonValue]], None],
    message: str,
) -> None:
    """Each candidate rejects invalid consumed and cross-field data."""
    # Given
    raw = sample_record(state)
    change(raw)

    # When / Then
    with pytest.raises(ValueError, match=message):
        construct_marker(candidate, json.dumps(raw).encode())


@pytest.mark.parametrize(
    "candidate",
    ["flat", "tagged", "dataclass"],
    ids=["flat-record", "tagged-record", "dataclass-union"],
)
@pytest.mark.parametrize(
    "data, cause",
    [(b"{", json.JSONDecodeError), (b"\xff", UnicodeDecodeError)],
    ids=["json-syntax", "utf8"],
)
def test_each_candidate_preserves_external_parse_cause(
    candidate: Candidate, data: bytes, cause: type[Exception]
) -> None:
    """Each candidate parse keeps JSON decoding exceptions as causes."""
    # Given
    encoded = data

    # When / Then
    with pytest.raises(ValueError, match="malformed sandbox metadata") as caught:
        construct_marker(candidate, encoded)
    assert isinstance(caught.value.__cause__, cause)


def test_file_read_failure_preserves_external_cause(tmp_path: Path) -> None:
    """Marker read failures become contextual values with their cause retained."""
    # Given
    directory = tmp_path / "marker.json"
    directory.mkdir()

    # When / Then
    with pytest.raises(ValueError, match="malformed sandbox metadata") as caught:
        read_metadata_file(directory)
    assert isinstance(caught.value.__cause__, IsADirectoryError)


def test_python_patterns_and_freezing_do_not_validate_or_deep_freeze_values() -> None:
    """Typed declarations and frozen outer records do not validate child values."""
    # Given
    mutable_extensions: dict[str, JsonValue] = {"key": [1]}
    record = DataclassRecord(
        1,
        "0123456789abcdef0123456789abcdef",
        Owner("", "", ""),
        DestinationIdentity(0, 0),
        Preparing(),
        mutable_extensions,
    )

    # When
    mutable_extensions["key"] = [2]
    is_int = matches_int_pattern(True)

    # Then
    assert record.extensions["key"] == [2]
    assert is_int


def test_complete_candidate_constructors_reject_invalid_direct_values() -> None:
    """Typed annotations do not enforce a complete runtime record boundary."""
    with pytest.raises(ValueError, match="malformed sandbox destination identity"):
        DataclassRecord(
            1,
            "0123456789abcdef0123456789abcdef",
            Owner("", "", ""),
            DestinationIdentity(0, -1),
            Preparing(),
            {},
        )
    invalid_flat = FlatRecord(
        schema_version=1,
        generation="0123456789abcdef0123456789abcdef",
        common_dir="",
        project="",
        base="",
        destination_device=0,
        destination_inode=-1,
        state="preparing",
    )
    with pytest.raises(ValueError, match="malformed sandbox destination identity"):
        FlatMarker(invalid_flat, {})
