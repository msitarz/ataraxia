# 5. Review completed handoffs once

Date: 2026-10-01

## Status

Accepted

Amended by
[13. Use Sol-low for all leaves](0013-use-sol-low-for-all-leaves.md).

Amended by
[17. Review local artifacts before PR publication](0017-review-local-artifacts-before-pr-publication.md).

## Context

Continuous polling and partial review can surface issues earlier, but status
polling, partial-diff inspections, fragmented corrections, and duplicate
checks add coordination overhead. The maintainer needs a completed result that
is quick to review.

## Decision

Give one focused handoff, then wait for the completed artifact or a blocker.
Accept later feedback in exchange for less polling: review the completed diff
once against acceptance and owner guidance, then send consolidated findings to
the same Luna session. Rerun focused checks only when
a change, failure, or unresolved concern warrants it. A draft PR means Luna's
work is complete and awaits orchestrator review; mark it ready only after the
independent review and correction loop pass. Ready requests human review; it
does not imply approval, merge, or successful CI.

## Consequences

The loop trades earlier feedback for less coordination; independent
orchestrator review and human review and merge gates remain. See
[orchestrator handoffs](../orchestrator.md),
[PR #83](https://github.com/msitarz/ataraxia/pull/83), and
[PR #84](https://github.com/msitarz/ataraxia/pull/84).
