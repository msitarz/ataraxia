# Define outcome contracts

## Purpose

Let a Work express one outcome with verifiable acceptance conditions and
inherited constraints.

## Goals

- Make a Work's completion and place in the larger design understandable
  quickly.
- Keep shared guarantees visible without repeating them in every child.

## Inherited constraints

Apply the [parent constraints](../README.md#inherited-constraints).

## Acceptance criteria

### **AC-1 DONE** One Work has one understandable outcome

The Work template, definition, and sizing guidance let a reader understand a
coherent outcome, its acceptance conditions, inherited constraints, and
relationship to architecture in about five minutes. Acceptance criteria describe
verifiable conditions or behaviors of that single outcome; Given/When/Then is
optional. Several acceptance conditions do not require several Works, and the
full implementation diff remains subject to substantive review without a time
cap. Compatible headings and checker syntax remain usable.

Conditions cover relevant success, failure or refusal, and preservation or
compatibility guarantees. Several scenarios may verify the same guarantee
without each becoming a criterion. Non-runtime acceptance conditions remain
valid for guidance, Investigations, and Evaluations; behavioral wording is not
required when the outcome is an inspectable artifact or finding.

Independently assessable guarantees have separate criteria; parallel conditions
of one guarantee may use bullets within that criterion. This distinction does
not impose a criterion quota or require more child Works.

### **AC-2 DONE** Shared constraints have an accountable verification scope

Parent contracts own essential shared concepts, invariants, responsibilities,
dependency direction, and effect limits without predefining every signature.
Children link to inherited constraints separately from local acceptance
criteria. Guidance shows where a non-functional requirement is verified locally,
architecturally, or at the system level; a quantitative threshold includes
workload and measurement conditions. Parent acceptance checks global guarantees
and composition rather than merely collecting child completion statuses.

## Dependencies

- DONE [Retire the cleanup process](../retire-cleanup/README.md): remove
  prescribed Work closure and post-merge Git cleanup procedures while preserving
  artifacts.

## Links

- [Work template](../../../work-contract-template.md),
  [Work definition](../../../work-definition.md),
  [Work workflow](../../../workflow.md), and
  [Work acceptance](../../../acceptance-tracing.md): authoritative contract,
  sizing, and acceptance owners.
- [Orchestrator guidance](../../../orchestrator.md): expected-scope and
  actual-diff review reminders to align.
