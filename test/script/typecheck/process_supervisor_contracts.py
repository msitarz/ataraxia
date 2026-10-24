# SPDX-License-Identifier: Apache-2.0
from typing import assert_never, assert_type

from script.process_supervisor import (
    AttemptObservation,
    AttemptResult,
    Completed,
    IncompleteAttempt,
    InfrastructureFailure,
    OutputLimitExceeded,
    TimedOut,
)


def contracts(observation: AttemptObservation, result: AttemptResult) -> None:
    incomplete = IncompleteAttempt(observation, None)
    assert_type(incomplete.exit_status, int | None)
    assert_type(TimedOut(observation, None), TimedOut)
    assert_type(OutputLimitExceeded(observation, 2), OutputLimitExceeded)
    assert_type(
        InfrastructureFailure(observation, 2, "OSError", "read failed"),
        InfrastructureFailure,
    )
    Completed(observation, 0)

    match result:
        case Completed(observation=completed_observation, exit_status=status):
            assert_type(completed_observation, AttemptObservation)
            assert_type(status, int)
        case TimedOut(exit_status=status):
            assert_type(status, int | None)
        case OutputLimitExceeded(exit_status=status):
            assert_type(status, int | None)
        case InfrastructureFailure(error_type=error_type, exit_status=status):
            assert_type(error_type, str)
            assert_type(status, int | None)
        case _ as unreachable:
            assert_never(unreachable)
