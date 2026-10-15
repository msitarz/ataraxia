# 26. Keep evidence at its source

Date: 2026-10-15

## Status

Accepted

Amends
[15. Use CI results as evidence of mechanical checks](0015-use-ci-results-as-evidence-of-mechanical-checks.md)
to extend the evidence-placement rule to contracts, commit messages, and
maintainer handoffs. Its CI, PR, independent-review, and merge rules remain.

## Context

Copying test output or check inventories into delivery prose adds reading work
and creates another representation of results that can become stale. The
maintainer needs the changed artifact and trustworthy evidence, rather than
repeated execution transcripts.

## Decision

Keep implementation test results in CI; local runs support preparation and
debugging. Guidance is assessed from the changed document. Investigations retain
findings and applicable execution results as artifacts; Evaluations retain the
results required by their declared protocol. The maintainer accepts outcomes,
with agent review preparing that decision.

Do not copy test output or check inventories into contracts, commit messages,
or maintainer handoffs. Report material failures and limitations concisely.
Current rules belong to [Work acceptance](../acceptance-tracing.md#evidence)
and [check policy](../validation.md).

## Consequences

Reviewers inspect source records instead of relying on agent-written summaries
as proof. They may need to consult CI or supporting artifacts rather than one
consolidated report. Investigation findings and protocol-defined results remain
useful artifacts; the rule removes duplicate test reporting, not the evidence.
The [guidance Work](../feat/work-contract-migration/guidance/README.md) carries
this change without altering the current cleanup sequence.
