# 31. Define outcome contracts and size for understanding

Date: 2026-10-22

## Status

Accepted

Amends
[3. Size Works for maintainer review](0003-size-works-for-maintainer-review.md)
for the five-minute heuristic, and
[23. Use readable README contracts](0023-use-readable-readme-contracts.md)
for acceptance criteria.

## Context

The prior sizing rule applied the five-minute target to the complete expected
change and actual diff, while the contract rule described one observable outcome
per criterion. This could conflate understanding a Work's intent with reviewing
its implementation, and could encourage separate criteria for scenarios of one
guarantee. The outcome-driven guidance Work requires one coherent outcome per
Work, verifiable acceptance conditions, inherited constraints, and a substantive
review sized to the change.

## Decision

Give each Work one coherent outcome. Its acceptance criteria follow these
rules:

- Describe independently assessable guarantees or conditions for the outcome.
- Allow several scenarios to establish one guarantee.
- Do not set a criterion quota.

Keep inherited constraints separate from local criteria. Parent contracts
establish these shared rules:

- Define concepts, invariants, responsibilities, dependency direction, and
  effect limits.
- Child contracts link to shared constraints and may add local constraints
  without weakening them.
- State whether inherited non-functional requirements are verified locally,
  architecturally, or at system level.
- Include workload and measurement conditions with quantitative thresholds.
- Have parent acceptance check global guarantees across the composition rather
  than only aggregate child completion.

Use the five-minute heuristic to make the outcome, acceptance conditions,
inherited constraints, scope, and architectural relationship quick to
understand. The heuristic does not cap substantive implementation review.

Scope and cohesion still bound a leaf. A concise contract cannot hide an
unbounded outcome or omit consequential detail. Given/When/Then is optional.
Non-runtime acceptance conditions remain valid for guidance, Investigations,
and Evaluations.

Apply the [shared writing standard](../README.md#writing) to Work contracts and
guidance. Documentation review assesses readability alongside meaning and
completeness.

## Consequences

The [Work contract template](../work-contract-template.md),
[Work definition](../work-definition.md),
[Work scope and sizing](../workflow.md#scope-and-sizing),
[Work acceptance](../acceptance-tracing.md), and
[orchestrator guidance](../orchestrator.md) own the current rules. The
[outcome-contract Work](../feat/outcome-driven-guidance/outcome-contracts/README.md)
delivers these changes and remains subject to independent review and parent
composition. Maintainer review, merge authority, and final-head CI remain in
force.
