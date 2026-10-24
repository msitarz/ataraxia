# SPDX-License-Identifier: Apache-2.0
from script.process_supervisor import AttemptObservation, Completed


def completed_requires_an_observed_exit_status(observation: AttemptObservation) -> None:
    Completed(observation, None)  # E: is not assignable
