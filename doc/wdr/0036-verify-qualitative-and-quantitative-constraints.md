# 36. Verify qualitative and quantitative constraints appropriately

Date: 2026-10-22

## Status

Accepted

Amends
[31. Define outcome contracts and size for understanding](0031-define-outcome-contracts-and-size-for-understanding.md)
for how inherited non-functional requirements state verification scope,
responsibility, and quantitative measurement conditions.

## Context

WDR 31 requires verification scope for inherited non-functional requirements
and workload and measurement conditions with quantitative thresholds. The
wording can be read to require numeric thresholds and measurement conditions
for qualitative constraints as well, although constraints such as purity or
dependency direction need verification but have no useful numeric target.

## Decision

- For every inherited non-functional requirement, state its verification scope
  and responsible verifier.
- For a quantitative requirement, state its threshold and the workload and
  measurement conditions needed to interpret it.
- For a qualitative constraint, name an appropriate verification method and
  scope; do not require a numeric target.
- Parent acceptance verifies system-level guarantees across the integrated
  result, including composition.
- This clarification does not weaken inherited constraints or make planned
  verification evidence of a completed outcome.

## Consequences

The [Work contract template](../work-contract-template.md) owns current
authoring instructions, and [Work acceptance](../acceptance-tracing.md) owns
criterion evidence. The
[Define outcome contracts Work](https://github.com/msitarz/ataraxia/blob/b703fa815a28f338fc2e69918a8351a455afb39e/doc/feat/outcome-driven-guidance/outcome-contracts/README.md)
carries the related context.
