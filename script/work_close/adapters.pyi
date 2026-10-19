# SPDX-License-Identifier: Apache-2.0
"""Concrete read boundary; depends on the planning consumer, never vice versa."""

from dataclasses import dataclass
from pathlib import Path

from script.markdown.model import MarkdownParser
from script.work_close.model import ClosureRequest
from script.work_close.planning import ClosureObservation

@dataclass(frozen=True)
class GitHubClosureReader:
    """Read local Git and GitHub metadata through read-only subprocesses.

    Composition injects the repository Markdown parser. This adapter owns Git
    and gh executable invocation, raw JSON validation and reference discovery.
    It supports only GitHub initially; host metadata never proves chat consent
    or semantic acceptance. Reuse contract discovery containment/read behavior
    only after rejecting directory selectors and empty/default-all selection.
    """

    root: Path
    markdown: MarkdownParser

    def observe(self, request: ClosureRequest, /) -> ClosureObservation:
        """Normalize repository, PR, selected contracts and live references.

        Raises:
            ClosurePlanningError: Git/gh/IO/Markdown fails, metadata is invalid,
                paths escape containment, or observations change during reads.
                Preserve expected low-level errors as exception causes.
        """
        ...
