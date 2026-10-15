# 24. Assess outcomes without per-criterion plans

Date: 2026-10-15

## Status

Accepted

Amends
[21. Publish after local Work acceptance](0021-publish-after-local-work-acceptance.md)
for declared per-criterion validation methods. Local acceptance, independent
review, publication, and latest-head CI responsibilities remain in force.

## Context

Per-criterion Validation clauses often repeated instructions to run tests and
checks. Detailed outcomes already describe success, including failure boundaries
and measurement conditions, while testing guidance owns check selection.
Maintaining another plan beside each outcome increased reading and editing work.

## Decision

Assess criteria against their stated outcomes without mandatory per-criterion
Validation or Verification plans. Put thresholds and conditions defining success
in the outcome. Choose appropriate checks using changed behavior and existing
coverage; an AC does not automatically require a new test. Preserve observed
evidence and independent review under
[Work acceptance](../acceptance-tracing.md).

Keeping fixed per-AC methods offers an explicit recipe, but repeats common
policy and couples the contract to a particular checking approach. Removing the
recipe requires judgment about sufficient evidence; it does not make plans,
declaration checks, or unexecuted tests proof of success. Evaluation protocols
remain required by [their owner](../evaluation.md).

## Consequences

Contracts describe delivered results rather than routine execution instructions.
Local evidence can establish acceptance before PR CI runs; the full latest-head
CI merge gate remains in [check policy](../validation.md). This changes neither
the current verification/cleanup commit sequence nor maintainer merge authority.
The [guidance Work](../feat/work-contract-migration/guidance/README.md) carries
the authoring and evidence changes.
