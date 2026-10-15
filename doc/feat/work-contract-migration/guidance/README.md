# Align guidance with readable Work contracts

## Purpose

Give humans and agents one concise route for authoring and reviewing the new
contracts without conflicting acceptance bookkeeping instructions.

## Goals

- Make the template authoritative for contract structure and outcome writing.
- Use one README contract per Work, with linked supporting artifacts.
- Remove repeated authoring instructions and obsolete marker/Validation rules.
- Preserve evidence, lifecycle, specialized Work, and review responsibilities.
- Fold exploratory implementation into Investigation rather than a separate
  Prototype Work kind.

## Non-Goals

- Change unrelated engineering or testing policies, agent roles, or delivery
  gates.
- Replace markers with mandatory per-AC test inventories or review reports.

## Acceptance criteria

### **AC-1 DONE** One owner for authoring instructions

Work definition, definer guidance, and task routing lead to the template rather
than repeat its section instructions or prohibit its required headings. Work
definition retains only useful context and specialized Work requirements that
the template does not supply.
General repair rules remain at their existing owner. Redundant historical
examples and repeated explanations are removed without losing requirements or
reading routes.

### **AC-2 TODO** Evidence assessed without mandatory validation plans or markers

Acceptance/evidence guidance defines the evidence used for implementation,
guidance, Investigation, and Evaluation outcomes, with maintainer acceptance and
independent review responsibilities explicit. It does not require Validation
clauses, covers decorators, or retired selection commands. Tests are chosen for
changed behavior and existing coverage; an AC does not automatically require a
new test. Measurements and conditions that define success belong in outcomes.
Existing CI, maintainer review, and verification/cleanup commit gates remain
explicit.

### **AC-3 TODO** Consistent routes and vocabulary

The guidance owners identified by the inventory, including glossary, evaluation,
executor, orchestrator, test ownership, and Make reminders, agree on the new
contract and evidence responsibilities. Links to moved/removed sections remain
valid. The template is discoverable through documentation ownership and task
routing, without making unrelated guidance mandatory reading.

### **AC-4 TODO** Lasting workflow decision recorded

WDRs record adopting README-only outcome contracts, retiring test-to-AC
bookkeeping, and folding Prototype into Investigation, with meaningful
tradeoffs and links to current owners. Historical
WDRs remain intact apart from required amendment/supersession metadata and links
under the existing decision-record lifecycle. The records do not substitute
for current guidance or claim implementation is complete.

### **AC-5 DONE** Prototyping is an Investigation method

Investigation owns bounded feasibility questions that need exploratory
implementation. Work definition, workflow reading routes, and the shared
glossary no longer define or route to a separate Prototype Work kind. The
Investigation contract states implementation limits and required observable
evidence; its results include unsuccessful attempts and distinguish observations
from assumptions. Production adoption requires a separate reviewed contract
covering missing production and integration requirements. Existing historical
references retain their original meaning.

### **AC-6 TODO** One README contract per Work

Work definition and acceptance guidance identify `README.md` as the Work
contract, without offering separate specification or design contracts.
Investigation findings and Evaluation protocols/results can remain linked
supporting artifacts. Migration contracts use this distinction consistently;
historical inventory observations and decision rationale remain intact. The
acceptance-tooling Work owns removing obsolete alternate-contract support.

## Dependencies

- [Completed migration inventory](../inventory.md): supplies affected owners,
  references, and preservation boundaries.

## Links

- [Template](../../../work-contract-template.md): authoring owner.
- [WDR workflow](../../../wdr-workflow.md): decision recording and history.
- [Initial inventory](../inventory.md): starting guidance surfaces.
