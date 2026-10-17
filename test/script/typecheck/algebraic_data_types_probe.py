# SPDX-License-Identifier: Apache-2.0
"""Locked-checker assertions against the executable investigation model."""

from typing import assert_never, assert_type

from test.script.unit.test_adt_investigation_probe import (
    DataclassRecord,
    Failed,
    FailedRecord,
    FailureDiagnostics,
    FlatMarker,
    Lifecycle,
    Marker,
    Preparing,
    Ready,
    TaggedMarker,
    TaggedRecord,
    construct_marker,
    dataclass_failure_details,
    failure_status,
    transition_ready,
)


def flat_missing_variant(marker: FlatMarker) -> None:
    match marker.owned["state"]:
        case "preparing" | "ready":
            return None
        case _:
            assert_never(marker.owned["state"])  # E: is not assignable


def tagged_missing_variant(marker: TaggedMarker) -> None:
    match marker.owned["state"]:
        case "preparing" | "ready":
            return None
        case _:
            assert_never(marker.owned["state"])  # E: is not assignable


def dataclass_missing_variant(state: Lifecycle) -> None:
    match state:
        case Preparing() | Ready():
            return None
        case _:
            assert_never(state)  # E: is not assignable


def tagged_narrowed_diagnostics(marker: TaggedMarker) -> str:
    if marker.owned["state"] == "failed":
        assert_type(marker.owned, FailedRecord)
        return marker.owned["failure_status"]
    return ""


def mapping_pattern_does_not_narrow(record: TaggedRecord) -> str | None:
    match record:
        case {"state": "failed", "failure_status": status}:
            return status  # E: not assignable
        case {"state": "preparing"} | {"state": "ready"}:
            return None
        case _:
            return None


def checker_contracts(marker: Marker, record: DataclassRecord) -> None:
    assert_type(construct_marker("flat", b"{}"), Marker)
    assert_type(failure_status(marker), str | None)
    assert_type(transition_ready(marker), Marker)
    assert_type(dataclass_failure_details(record.lifecycle), FailureDiagnostics | None)
    assert_type(Failed(FailureDiagnostics("stage", "status", "out", "err")), Failed)
    assert_type(record.lifecycle, Lifecycle)
