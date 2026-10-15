# Align guidance with readable Work contracts

## Purpose

Give humans and agents one concise route for authoring and reviewing the new
contracts without conflicting acceptance bookkeeping instructions.

## Goals

- Make the template authoritative for contract structure and outcome writing.
- Remove repeated authoring instructions and obsolete marker/Validation rules.
- Preserve evidence, lifecycle, specialized Work, and review responsibilities.

## Non-Goals

- Change unrelated engineering or testing policies, agent roles, or delivery
  gates.
- Replace markers with mandatory per-AC test inventories or review reports.

## Acceptance criteria

### **AC-1 TODO** One owner for authoring instructions

Work definition, definer guidance, and task routing lead to the template rather
than repeat its section instructions or prohibit its required headings. Work
definition retains only useful context and specialized Investigation,
Evaluation, and Prototype requirements that the template does not supply.
General repair rules remain at their existing owner. Redundant historical
examples and repeated explanations are removed without losing requirements or
reading routes.

### **AC-2 TODO** Evidence assessed without mandatory validation plans or markers

Acceptance/evidence guidance requires observed evidence and independent review
before DONE, without requiring Validation clauses, covers decorators, or retired
selection commands. Tests are chosen for changed behavior and existing coverage;
an AC does not automatically require a new test. Measurements and conditions
that define success belong in outcomes. Existing CI, maintainer review, and
verification/cleanup commit gates remain explicit.

### **AC-3 TODO** Consistent routes and vocabulary

The guidance owners identified by the inventory, including glossary, evaluation,
executor, orchestrator, test ownership, and Make reminders, agree on the new
contract and evidence responsibilities. Links to moved/removed sections remain
valid. The template is discoverable through documentation ownership and task
routing, without making unrelated guidance mandatory reading.

### **AC-4 TODO** Lasting workflow decision recorded

A WDR records adopting readable outcome contracts and retiring test-to-AC
bookkeeping, with meaningful tradeoffs and links to current owners. Historical
WDRs remain intact apart from required amendment/supersession metadata and links
under the existing decision-record lifecycle. The record does not substitute
for current guidance or claim implementation is complete.

## Dependencies

- **TODO** [Migration inventory](../inventory/README.md): supplies affected
  owners, references, and preservation boundaries.

## Links

- [Template](../../../work-contract-template.md): authoring owner.
- [WDR workflow](../../../wdr-workflow.md): decision recording and history.
- [Initial inventory](../inventory.md): starting guidance surfaces.
