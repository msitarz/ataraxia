# 5. Review completed handoffs once

Date: 2026-10-01

## Status

Accepted

## Context

Routine status polling, partial-diff inspections, fragmented corrections, and
duplicate checks add coordination overhead to small Works. The maintainer
needs a completed result that is quick to review.

## Decision

Give one focused handoff, then wait for the completed artifact or a blocker.
Review the completed diff once against acceptance and owner guidance, and send
consolidated findings to the same Luna session. Rerun focused checks only when
a change, failure, or unresolved concern warrants it. A draft PR means Luna's
work is complete and awaits orchestrator review; mark it ready only after the
independent review and correction loop pass. Ready requests human review; it
does not imply approval, merge, or successful CI.

## Consequences

The handoff and review loop has explicit states and avoids routine polling;
independent orchestrator review and human review and merge gates remain. See
[orchestrator handoffs](../orchestrator.md),
[PR #83](https://github.com/msitarz/ataraxia/pull/83), and
[PR #84](https://github.com/msitarz/ataraxia/pull/84).
