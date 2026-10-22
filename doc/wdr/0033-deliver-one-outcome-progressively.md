# 33. Deliver one outcome progressively

Date: 2026-10-22

## Status

Accepted

## Context

Outcome-sized Works can benefit from executable architecture and behavioral
evidence before every leaf operation is complete. Treating these steps as
mandatory phases or separate Works would add process without making the outcome
more coherent. At the same time, typed declarations, stubs, and test intentions
must not be mistaken for delivered behavior.

## Decision

Progressive delivery is allowed within one coherent Work, subject to these
rules:

- Let behavior and tests progress in increments within that Work.
- Use typed composition and an optional
  [walking skeleton](../engineering.md#progressive-implementation) when they
  help expose integration risks.
- Keep sequencing and effect ownership real.
- Review actual data flow, including dynamic mappings that static checks may
  miss.
- Require observed evidence at the level claimed for acceptance.
- Keep existing boundary validation, construction, pure-decision, live-effect,
  review, and delivery-gate rules in force.

## Consequences

[Executor guidance](../executor.md) routes to the progression rules in
[engineering guidance](../engineering.md#progressive-implementation), which
owns optional implementation increments and the walking skeleton technique.
[Engineering review](../engineering-review.md) owns data-flow review,
[testing guidance](../testing.md) owns test-intent and assertion review, and
[Work acceptance](../acceptance-tracing.md) owns the meaning of evidence.
The
[progressive-delivery Work](../feat/outcome-driven-guidance/progressive-delivery/README.md)
delivers these changes. Work splitting, architecture maturity, and any new scope
or maintainer decision retain their existing gates. Maintainer review and merge
authority, independent review, and final-head CI remain in force.
