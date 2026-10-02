# 11. Keep verification plans distinct from results

Date: 2026-10-02

## Status

Proposed

Amends
[9. Require verified evidence for Work completion](0009-require-verified-work-completion.md).

## Context

The accepted completion rule requires results beside criteria, while current
guidance can be read to replace a criterion's `Verification:` method with its
result. That conflates an execution plan with evidence and can make a prose
edit appear to establish completion.

## Decision

Keep `Verification:` as the planned method that guides the executor and
reviewer, unchanged when a criterion moves from `TODO` to `DONE`. It does not
establish coverage, observed results, or completion. Record applicable observed
evidence beside the criterion and independently review it before `DONE`.
Automated behavior needs applicable marked tests and execution results;
measurements and trials need recorded observations or artifacts; manual
judgment needs independent review of the actual changed artifact, with the
result in the PR. A declaration check does not establish coverage or results.
Review completion remains distinct from maintainer approval and merge.

The current procedure remains in
[acceptance tracing](../acceptance-tracing.md); this amendment clarifies its
evidence semantics without adding result fields or changing the two-commit
delivery boundary.

## Consequences

Keep the planned method beside each criterion and record its actual outcome
beside that criterion under the existing delivery procedure. Preserve the
contract and evidence commit before the separate contract-removal and parent-map
commit. This makes method declarations useful for planning while requiring
observed and reviewed evidence for completion. See
[Work lifecycle](../workflow.md), [orchestrator handoffs](../orchestrator.md),
and the
[verification-plan Work](../feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/verification-plan/README.md).
