# SPDX-License-Identifier: Apache-2.0
"""One-time locked-checker probe for complete record candidates."""

from dataclasses import dataclass, replace
from typing import Literal, NotRequired, TypedDict, assert_never, assert_type

type JsonValue = (
    str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None
)


class FlatRecord(TypedDict):
    schema_version: int
    generation: str
    common_dir: str
    project: str
    base: str
    destination_device: int
    destination_inode: int
    state: Literal["preparing", "ready", "failed"]
    failure_stage: NotRequired[str]
    failure_status: NotRequired[str]
    failure_stdout: NotRequired[str]
    failure_stderr: NotRequired[str]


def flat_failure_details(record: FlatRecord) -> str | None:
    match record["state"]:
        case "failed":
            return record.get("failure_status")
        case "preparing" | "ready":
            return None
        case _:
            assert_never(record["state"])


def flat_missing_failed(record: FlatRecord) -> None:
    match record["state"]:
        case "preparing" | "ready":
            return None
        case _:
            assert_never(record["state"])  # E: is not assignable


def flat_ready(record: FlatRecord) -> FlatRecord:
    if record["state"] != "preparing":
        raise ValueError("sandbox preparation state cannot be reassigned")
    return {
        "schema_version": record["schema_version"],
        "generation": record["generation"],
        "common_dir": record["common_dir"],
        "project": record["project"],
        "base": record["base"],
        "destination_device": record["destination_device"],
        "destination_inode": record["destination_inode"],
        "state": "ready",
    }


class SharedRecord(TypedDict):
    schema_version: int
    generation: str
    common_dir: str
    project: str
    base: str
    destination_device: int
    destination_inode: int


class PreparingRecord(SharedRecord):
    state: Literal["preparing"]


class ReadyRecord(SharedRecord):
    state: Literal["ready"]


class FailedRecord(SharedRecord):
    state: Literal["failed"]
    failure_stage: str
    failure_status: str
    failure_stdout: str
    failure_stderr: str


type TaggedRecord = PreparingRecord | ReadyRecord | FailedRecord


def tagged_failure_details(record: TaggedRecord) -> str | None:
    match record["state"]:
        case "failed":
            assert_type(record, FailedRecord)
            return record["failure_status"]
        case "preparing" | "ready":
            return None
        case _:
            assert_never(record["state"])


def tagged_ready(record: PreparingRecord) -> ReadyRecord:
    return {
        "schema_version": record["schema_version"],
        "generation": record["generation"],
        "common_dir": record["common_dir"],
        "project": record["project"],
        "base": record["base"],
        "destination_device": record["destination_device"],
        "destination_inode": record["destination_inode"],
        "state": "ready",
    }


def tagged_missing_failed(record: TaggedRecord) -> None:
    match record["state"]:
        case "preparing" | "ready":
            return None
        case _:
            assert_never(record["state"])  # E: is not assignable


def mapping_pattern_does_not_narrow(record: TaggedRecord) -> str | None:
    match record:
        case {"state": "failed", "failure_status": status}:
            return status  # E: not assignable
        case {"state": "preparing"} | {"state": "ready"}:
            return None
        case _:
            return None


@dataclass(frozen=True)
class FailureDiagnostics:
    stage: str
    status: str
    stdout: str
    stderr: str


@dataclass(frozen=True)
class Preparing:
    pass


@dataclass(frozen=True)
class Ready:
    pass


@dataclass(frozen=True)
class Failed:
    diagnostics: FailureDiagnostics


type Lifecycle = Preparing | Ready | Failed


@dataclass(frozen=True)
class Owner:
    common_dir: str
    project: str
    base: str


@dataclass(frozen=True)
class DestinationIdentity:
    device: int
    inode: int


@dataclass(frozen=True)
class DataclassRecord:
    schema_version: int
    generation: str
    owner: Owner
    destination: DestinationIdentity
    lifecycle: Lifecycle
    extensions: dict[str, JsonValue]


def dataclass_failure_details(state: Lifecycle) -> FailureDiagnostics | None:
    match state:
        case Failed(diagnostics=details):
            return details
        case Preparing() | Ready():
            return None
        case _:
            assert_never(state)


def dataclass_ready(record: DataclassRecord) -> DataclassRecord:
    if not isinstance(record.lifecycle, Preparing):
        raise ValueError("sandbox preparation state cannot be reassigned")
    return replace(record, lifecycle=Ready())


def dataclass_missing_failed(state: Lifecycle) -> None:
    match state:
        case Preparing() | Ready():
            return None
        case _:
            assert_never(state)  # E: is not assignable


def check_contracts(
    flat: FlatRecord,
    tagged: TaggedRecord,
    dataclass_record: DataclassRecord,
    lifecycle: Lifecycle,
) -> None:
    assert_type(flat_failure_details(flat), str | None)
    assert_type(flat_ready(flat), FlatRecord)
    assert_type(tagged_failure_details(tagged), str | None)
    assert_type(
        tagged_ready(
            PreparingRecord(
                schema_version=1,
                generation="0" * 32,
                common_dir="/repo/.git",
                project="ataraxia",
                base="a" * 40,
                destination_device=1,
                destination_inode=2,
                state="preparing",
            )
        ),
        ReadyRecord,
    )
    assert_type(dataclass_failure_details(lifecycle), FailureDiagnostics | None)
    assert_type(dataclass_ready(dataclass_record), DataclassRecord)
    assert_type(mapping_pattern_does_not_narrow(tagged), str | None)
