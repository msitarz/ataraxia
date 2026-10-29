# SPDX-License-Identifier: Apache-2.0
"""Coordinator execution through the real local process supervisor."""

from dataclasses import replace
from pathlib import Path
import sys

from script.eval.runner.coordinator import Coordinator
from script.process_supervisor import (
    AttemptRequest,
    AttemptResult,
    DispatchStop,
    call_supervisor,
    run_attempt,
)
from test.script.unit.eval.test_coordinator import Sink, prepare
from test.script.unit.eval.test_coordinator_calls import Classifier, Clock, NoQuota


async def supervised(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
    """Use the production supervisor around a controlled local process."""
    return await call_supervisor(request, run_attempt, stop)


async def test_coordinator_retains_supervised_process_output(tmp_path: Path) -> None:
    # Given
    bound, store = await prepare(tmp_path, 1)
    effective = bound.calls[0]
    request = replace(
        effective.request,
        argv=("/usr/bin/env", "-i", sys.executable, "-c", "print('controlled')"),
        cwd=tmp_path,
    )
    bound = replace(bound, calls=(replace(effective, request=request),))

    # When
    record = await Coordinator(
        bound, store, supervised, Classifier(), NoQuota(), Clock(), Sink()
    ).run()

    # Then
    assert record.state == "complete"
    assert record.calls[0].attempts[0].exit_status == 0
    artifact = record.calls[0].attempts[0].stdout_artifact
    assert artifact is not None
    assert Path(artifact).read_bytes() == b"controlled\n"
