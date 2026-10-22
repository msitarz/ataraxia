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
relationship to architecture in about five minutes. Acceptance criteria:

- Describe verifiable conditions or behaviors of that single outcome.
- May use Given/When/Then, but do not require it.
- Cover relevant success, failure or refusal, and preservation or compatibility
  guarantees.
- May group several scenarios that verify the same guarantee.
- May describe non-runtime outcomes for guidance, Investigations, and
  Evaluations; an inspectable artifact or finding does not need behavioral
  wording.
- Give independently assessable guarantees separate criteria, while allowing
  parallel conditions of one guarantee within the same criterion.

Several acceptance conditions do not require several Works, and these rules do
not set a criterion quota or require more child Works. The full implementation
diff remains subject to substantive review without a time cap. Compatible
headings and checker syntax remain usable.

### **AC-2 DONE** Shared constraints have an accountable verification scope

Parent contracts own essential shared concepts, invariants, responsibilities,
dependency direction, and effect limits without predefining every signature.
Children link to inherited constraints separately from local acceptance
criteria. Guidance shows where a non-functional requirement is verified:

- Locally, architecturally, or at the system level.
- With workload and measurement conditions for a quantitative threshold.

Parent acceptance checks global guarantees and composition rather than merely
collecting child completion statuses.

### **AC-3 TODO** Work contracts and guidance use the shared writing standard

The documentation owner defines a shared writing standard for Work contracts
and guidance. The Work contract template links to that owner, and changed
contracts and guidance follow the standard. Documentation review assesses
readability alongside meaning and completeness.

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
