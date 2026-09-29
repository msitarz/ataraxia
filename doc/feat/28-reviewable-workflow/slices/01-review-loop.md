---
id: F28-01
kind: slice
parent: F28
status: proposed
approved_revision: null
---

# Adopt the review loop and document ownership

## Outcome and scope

Update owning guidance so discovery, definition, design, and execution produce
small artifacts and wait for explicit continuation approval. Adopt the
[overall contracts](../spec.md) and [document model](../design.md#documents-and-revisions).
This slice delivers guidance and templates; later slices deliver mechanical gates.

Update shared terms in the glossary, workflow behavior in `feat-workflow.md`,
document responsibilities in `documentation.md`, structural conventions in
`engineering.md`, and validation/publication routes in `CONTRIBUTING.md` when
their owner changes. Keep `AGENTS.md` a short routing table. Preserve the original
historical slices. Do not create an ADR for a template or routine helper choice.

The specification template has predictable places for the inspected baseline,
outcome, scope/non-goals, contracts and falsifiable invariants, acceptance IDs,
and delivery dependencies. Mark decisions settled, assumed, or open, with explicit
stop conditions for unresolved consequential choices. Keep status and evidence
in their owners. Each step names affected criteria, indicative paths, commands
once known, an exit condition, and the decision requested at review.

Define a lightweight discovery record and prototype promotion gap assessment.
Describe migration slices for rewrites, with explicit preserved behavior and
approved intentional changes. No separate experiment index entry is needed for
each run, and no production prototype adoption happens in this slice.

## Proposed iterations

Commit each changed, checked iteration and present it before the next dependent
iteration. Split further when the actual review burden exceeds the budget.

| Step | Concrete artifact and decision | Verification and proposed checkers |
| --- | --- | --- |
| 1 | A one-screen review artifact template and one worked discovery example; review what information is sufficient | Manual five-minute navigation/readability review; proposed required artifact fields and stable revision references |
| 2 | The continuation and material-change rules in their owning workflow section; review when an agent proceeds or stops | Walk through approval, correction, silence, new revision, and independent-work examples; proposed approval/history checks |
| 3 | Package template and ownership routes; review one small slice and one grouped feat | Relative links and planned YAML schemas; proposed rumdl headings/metadata checks and route checks |
| 4 | Structural review and discovery/promotion/migration guidance, reviewed as separate artifacts if needed | Check precise types, module ownership, scope and vocabulary; proposed rumdl/prose checks and investigated Ruff rules, with existing type/Tach checks unchanged |

`make verify-check` and `git diff --check` apply during guidance changes;
`make ci` is required for publication. Until the new tools exist, inspect the
proposed document checks explicitly rather than claim they ran.

## Acceptance criteria

| ID | Preconditions and action | Observable outcome | Verified by |
| --- | --- | --- | --- |
| AC-1 | Apply the template to discovery, specification, design, and code examples | Each exposes one result, directly accessible evidence, limits, a decision, and the next step | Recorded manual template walkthrough |
| AC-2 | Walk through approval and correction examples at named revisions | Guidance permits scoped corrections, requires approval for dependent continuation, and never treats checks or silence as approval | Manual walkthrough; later history-check fixtures |
| AC-3 | Open a new package and resume from its README | Authoritative contracts, design, consequential history, and next action are reachable without duplicate state | Link/schema checks once available; manual navigation |
| AC-4 | Review similar types, misplaced helpers, an experiment, and a rewrite proposal | Guidance preserves semantic distinctions, permits no refactor, and requires explicit promotion/migration gaps | Recorded structural and discovery walkthrough |

## Boundaries and next review

Guidance approval does not validate future behavior or language tooling. After
adoption, slice 02 investigates candidates one question at a time. Journal events
and approvals for this slice belong to the [parent journal](../journal.md).
