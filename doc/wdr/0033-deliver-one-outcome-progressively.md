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

Allow an outcome to progress through typed composition, optional stubbed leaves,
a thin executable path, and behavioral tests as useful within one coherent Work.
The composition must express real sequencing and effect ownership, and review
must inspect actual data flow, including dynamic mappings that static checks may
miss. Early test review may assess intent; acceptance still requires observed
evidence at the level claimed. Keep existing boundary validation, construction,
pure-decision, live-effect, review, and delivery-gate rules in force.

## Consequences

[Executor guidance](../executor.md) owns the delivery route,
[engineering guidance](../engineering.md) and
[engineering review](../engineering-review.md) own composition and data-flow
review, [testing guidance](../testing.md) owns test-intent and assertion review,
and [Work acceptance](../acceptance-tracing.md) owns the meaning of evidence.
The
[progressive-delivery Work](../feat/outcome-driven-guidance/progressive-delivery/README.md)
delivers these changes. Work splitting, architecture maturity, and any new scope
or maintainer decision retain their existing gates. Maintainer review and merge
authority, independent review, and final-head CI remain in force.
