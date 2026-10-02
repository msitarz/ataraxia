# 11. Keep verification plans distinct from results

Date: 2026-10-02

## Status

Accepted

Amends
[9. Require verified evidence for Work completion](0009-require-verified-work-completion.md).

## Context

WDR 9 requires manual evidence beside criteria, while current guidance can be
read to replace a criterion's `Verification:` method with its result. That
conflates an execution plan with evidence and can make a prose edit appear to
establish completion.

## Decision

Keep `Verification:` as the planned method that guides the executor and
reviewer, unchanged when a criterion moves from `TODO` to `DONE`. It does not
establish coverage, observed results, or completion. Independently review
applicable evidence before `DONE`.

Evidence stays where it is produced: applicable marked tests and selected
execution results in check or CI artifacts; measurement and trial observations
in existing reports or artifacts; manual judgment from review of the actual
changed artifact recorded in the PR. The reviewer verifies that this evidence
accounts for the criteria. Do not add per-criterion result fields, duplicate
results in the Work contract, or require a separate report or ledger. A
declaration check does not establish test coverage or observed or reviewed
results. Review completion remains distinct from maintainer approval and
merge.

The current procedure remains in
[acceptance tracing](../acceptance-tracing.md); this amendment changes where
manual results are recorded and clarifies evidence location without changing
the two-commit delivery boundary.

## Consequences

Keep planned methods and verified statuses in the retained contract, and
evidence locatable in its PR, Git, check results, or existing artifacts.
Preserve the contract and evidence commit before the separate contract-removal
and parent-map commit. This makes method declarations useful for planning while
requiring independently reviewed evidence for completion. See [Work
lifecycle](../workflow.md) and [orchestrator handoffs](../orchestrator.md).
