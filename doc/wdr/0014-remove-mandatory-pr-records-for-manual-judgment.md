# 14. Remove mandatory PR records for manual judgment

Date: 2026-10-03

## Status

Accepted

Amends
[11. Keep verification plans distinct from results](0011-keep-verification-plans-distinct-from-results.md).

Amended by
[15. Use CI results as evidence of mechanical checks](0015-use-ci-results-as-evidence-of-mechanical-checks.md).

## Context

WDR 11 requires recording manual judgment of a changed artifact in the PR. This
creates a separate recording obligation even when the independent review has
already occurred. [PR 131](https://github.com/msitarz/ataraxia/pull/131) removes
that obligation from [acceptance tracing](../acceptance-tracing.md).

## Decision

Require independent review of the changed artifact for manual judgment without
requiring a PR record or comment for each review. This amends only WDR 11's
manual-judgment placement rule. `Verification:` remains a plan, automated
evidence and trial observations remain in their source records, and independent
review of applicable evidence remains required before `DONE`.

## Consequences

Manual reviews no longer require a separate PR record. The verified
implementation/evidence commit with the retained contract and the later cleanup
commit remain required and must not be squashed. `DONE` still does not mean
maintainer approval or merge. Existing records remain intact.
