# SPDX-License-Identifier: Apache-2.0
"""Coordinator state; durable history and each in-flight fact have one owner."""

from asyncio import CancelledError
from dataclasses import dataclass
from typing import Literal

from script.eval.model import (
    WaitEvent,
    WaitRecord,
)
from script.process_supervisor import AttemptResult


@dataclass(frozen=True)
class WaitWrite:
    """A failed wait event and its pending final summary, if closing."""

    event: WaitEvent
    record: WaitRecord | None


@dataclass(frozen=True)
class StopReason:
    """First stop and original owner or leaf cancellation, if one occurs later.

    Internal sibling cancellations do not replace the primary control flow.
    Recording failure is retained and attached as cause when cancellation wins.
    """

    first: BaseException | AttemptResult
    cancellation: CancelledError | None
    cancellation_origin: Literal["owner", "leaf"] | None
    recording_failure: BaseException | None
