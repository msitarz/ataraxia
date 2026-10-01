# 10. Recover delegated handoffs

Date: 2026-10-01

## Status

Proposed

## Context

The accepted handoff loop limits polling and fragmented review, and existing
guidance already requires stopping and splitting when scope adds an independent
responsibility or exceeds the review target. It does not specify enough return
evidence to distinguish completion from a blocker or how to resume after a
cancelled or lost session. It also needs a stopping point for unresolved
corrections without weakening maintainer control over delegation.

## Decision

Require a return to identify its artifact, outcome, acceptance evidence, check
results and omissions, unresolved criteria, and blockers. Recover interrupted
work from its contract, parent map, branch or PR, and available results before
continuing. On out-of-scope discoveries, report findings and apply the existing
stop-and-split rule where its conditions hold. After a correction remains
unresolved, report the evidence and needed steering before resuming. Preserve
approval for the maintainer scope exception and for changing agent or reasoning
effort.

## Consequences

Returns and recovery take a concise reconstruction of state, while avoiding
routine polling and evidence journals. Current rules belong in
[orchestrator handoffs](../orchestrator.md); criterion status and coverage
semantics remain in [acceptance tracing](../acceptance-tracing.md). See the
trial-preparation
[parent Work](../feat/reviewable-workflow-v2/trial-preparation/README.md).
