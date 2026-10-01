# 6. Keep delivery evidence in PRs and Git

Date: 2026-09-30

## Status

Accepted

## Context

The maintainer reported that earlier evidence-SHA snapshots and append-only
journals caused context bloat, extra reading and writing, and bookkeeping and
CI-evidence commit loops. A structured log can make resumption and audit easier,
but updating it for each revision adds work to small, human-reviewed Works.

## Decision

Use PR discussion, Git history, and relevant check or CI results as delivery
evidence. Do not add routine append-only journals, per-revision result
snapshots, or evidence-only commit loops. Keep acceptance evidence sufficient
for review, and retain required checks, CI, and manual review. A Git SHA remains
appropriate when it locates useful evidence, such as in a bug report or ADR;
this choice does not ban useful SHA references.

## Consequences

Readers may need to reconstruct revision history from the PR and Git rather
than consult one centralized journal. See [Work lifecycle](../workflow.md),
[orchestrator handoffs](../orchestrator.md),
[validation policy](../validation.md), and
[PR #75](https://github.com/msitarz/ataraxia/pull/75).
