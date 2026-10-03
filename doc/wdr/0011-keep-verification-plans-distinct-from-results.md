# 11. Keep verification plans distinct from results

Date: 2026-10-02

## Status

Accepted

Amends
[9. Require verified evidence for Work completion](0009-require-verified-work-completion.md).

Amended by
[14. Remove mandatory PR records for manual judgment](0014-remove-mandatory-pr-records-for-manual-judgment.md).

## Context

WDR 9 places manual evidence beside criteria. This can conflate the planned
method with its result and make a prose edit look like proof of completion.

## Decision

Treat `Verification:` as a plan, not evidence. Manual judgment of the changed
artifact is recorded in the PR; evidence otherwise stays in its source records.
An independent reviewer checks applicable evidence before `DONE`. This amends
WDR 9's manual-evidence placement rule. Current requirements belong in
[acceptance tracing](../acceptance-tracing.md).

## Consequences

Manual outcomes move to PR review records; this avoids duplicating them in Work
contracts. The retained contract and evidence commit followed by separate
contract/map removal commit remain in force; do not squash these deliveries.
