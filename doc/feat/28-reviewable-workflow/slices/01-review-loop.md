---
id: F28-01
kind: slice
parent: F28
status: in progress
stage: awaiting-structural-review
approved_revision: "36edc546d33f63c130c930b65884c21f56fd3ec0"
issue: 30
pr: 31
branch: feat/reviewable-workflow-slice-01
base_branch: feat/reviewable-workflow
base_revision: "daf6d350f141387612d056a8dad60a731fb7a47d"
steps:
  - id: STEP-1
    issue: 32
    pr: 33
    branch: feat/reviewable-workflow-slice-01-step-01
    base_branch: feat/reviewable-workflow-slice-01
    base_revision: "9231d7164ec41835872bbd594b4e2b3770fbb1ce"
    stage: merged
  - id: STEP-2
    issue: 34
    pr: 35
    branch: feat/reviewable-workflow-slice-01-step-02
    base_branch: feat/reviewable-workflow-slice-01
    base_revision: "588cde5ba881b6e20d1dfc0d558ae710e3b6d264"
    stage: merged
  - id: STEP-3
    issue: 36
    pr: 37
    branch: feat/reviewable-workflow-slice-01-step-03
    base_branch: feat/reviewable-workflow-slice-01
    base_revision: "78a67e709c987d090c98b1aec671d0983e4f5811"
    stage: merged
  - id: STEP-5
    issue: 38
    pr: 39
    branch: feat/reviewable-workflow-slice-01-step-05
    base_branch: feat/reviewable-workflow-slice-01
    base_revision: "764e3e1f4cad43482c1847f78b88bc9153913bba"
    stage: merged
  - id: STEP-6
    issue: 40
    pr: 41
    branch: feat/reviewable-workflow-slice-01-step-06
    base_branch: feat/reviewable-workflow-slice-01
    base_revision: "004a6ba66d7422284d071a00a5bfa01f3cbd1f93"
    stage: merged
  - id: STEP-4
    issue: 42
    pr: 43
    branch: feat/reviewable-workflow-slice-01-step-04
    base_branch: feat/reviewable-workflow-slice-01
    base_revision: "36edc546d33f63c130c930b65884c21f56fd3ec0"
    stage: awaiting-review
---

# Adopt the review loop and document ownership

## Outcome and scope

Update owning guidance so discovery, definition, design, and execution produce
small artifacts and wait for explicit continuation approval. Adopt the
[overall contracts](../spec.md) and [document model](../design.md#documents-and-revisions).
This slice delivers guidance and templates; later slices deliver mechanical gates.

Adopt [delivery tracking and merge boundaries](../spec.md#delivery-tracking-and-merge-boundaries)
in the owning workflow and contribution guidance. Give the slice and each agreed
delivery step its own linked issue, branch and PR; step PRs target the slice,
and the slice PR targets the feat. Review integration through accepted child PRs
and actual acceptance evidence. The maintainer performs every merge.

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

Include visual companions in specification and design templates following the
[record contract](../spec.md#6-keep-records-small-and-authoritative). Use the
accepted views in this package as worked examples and inspect rendered behavior
and relationship views during the manual template walkthrough.

Include a journal-entry template following the
[entry and identity contract](../spec.md#journal-entries-and-session-identity).
Its first YAML block records kind and embedded native identity; prose carries
consequences and ordinary Markdown links. Show a decision and a revision-scoped
approval without session aliases or a registration step.

Define a lightweight discovery record and prototype promotion gap assessment.
Describe migration slices for rewrites, with explicit preserved behavior and
approved intentional changes. No separate experiment index entry is needed for
each run, and no production prototype adoption happens in this slice.

## Proposed iterations

Commit each changed, checked iteration and present it before the next dependent
iteration. Track it as a delivery step; dependent continuation also waits for its
reviewed merge into the slice. Split further when actual review burden exceeds
the budget. Corrections reuse the step issue and PR.

| Step | Concrete artifact and decision | Verification and proposed checkers |
| --- | --- | --- |
| 1 | A one-screen review artifact template and one worked discovery example; review what information is sufficient | Manual five-minute navigation/readability review; proposed required artifact fields and stable revision references |
| 2 | Continuation, material-change and step/slice PR rules in their owning guidance; review when an agent proceeds or stops | Walk through approval, correction, silence, changed revision, wrong PR base, pending merge and next-step examples; proposed tracking/approval/history checks |
| 3 | Package template, ownership routes and Mermaid companions; review one small slice and one grouped feat | Relative links, rendered views and planned YAML schemas; proposed rumdl headings/metadata checks and route checks |
| 5 | Overhead-reduction planning amendment; review validation selection, evidence reuse and lighter publishing before changing active guidance | Recorded step 3 baseline and docs/code invalidation walkthrough; later checker fixtures for selection and evidence provenance |
| 6 | Adopt the accepted overhead rules in workflow and contribution guidance; review whether draft publication and merge checks remain clear | Walk through navigation-only versus changed code inputs; affected document checks and current-head CI at merge |
| 4 | Structural review rule and two cases: similar types and a misplaced helper | Inspect meaning, invariants, precision and ownership; record a justified no-refactor result where appropriate; affected document checks |
| 7 | Discovery record and prototype promotion gap assessment, if agreed after step 4 | Walk through one bounded experiment and the gap to production; inspect links and metadata |
| 8 | Rewrite migration guidance, if agreed after step 7 | Walk through preserved behavior, intentional changes, comparison, cutover and retirement; inspect links and metadata |

Steps 5 and 6 preceded step 4. Rows 7 and 8 are outlines, not registered or
authorized steps; preserve all identities.

Follow [validation selection](../../../../CONTRIBUTING.md#validation-selection)
for draft publication and current-head merge evidence. Until the new tools
exist, inspect proposed document checks rather than claim they ran.

## Overhead-reduction amendment

First deliver an accepted planning amendment to the
[effort/validation contract](../spec.md#execution-effort-and-validation) and
[evidence design](../design.md#bounded-execution-and-evidence-reuse). Proposed
owner changes follow in a separately agreed delivery step. This amendment does
not change Makefile, hooks, CI, dependencies or the active publication procedure.

The initial execution target is ten minutes for routine bounded work, with an
obstacle/split proposal when exceeded. Review effort remains separately measured
through maintainer feedback. Use medium reasoning for this trial as requested;
no repository rule forces a model or effort setting.

Walk through two cases: a navigation-only edit can retain applicable application
test evidence while document checks rerun; a changed code/test/tool input
invalidates dependent evidence and triggers relevant checks. Exact check
dependencies, generic Markdown support and provenance validation need later
investigation/fixtures. Do not build temporary general checker infrastructure
for each documentation step or claim unrun checks passed.

## Acceptance criteria

| ID | Preconditions and action | Observable outcome | Verified by |
| --- | --- | --- | --- |
| AC-1 | Apply the template to discovery, specification, design, and code examples | Each exposes one result, directly accessible evidence, limits, a decision, and the next step | Recorded manual template walkthrough |
| AC-2 | Walk through approval and correction examples at named revisions | Guidance permits scoped corrections, requires approval for dependent continuation, and never treats checks or silence as approval | Manual walkthrough; later history-check fixtures |
| AC-3 | Open a new package and resume from its README | Authoritative contracts, design, consequential history, and next action are reachable without duplicate state | Link/schema checks once available; manual navigation |
| AC-4 | Review similar types, misplaced helpers, an experiment, and a rewrite proposal | Guidance preserves semantic distinctions, permits no refactor, and requires explicit promotion/migration gaps | Recorded structural and discovery walkthrough |
| AC-5 | Track a slice and two dependent delivery steps through review and integration | Own issues/PRs target the correct parents; corrections reuse tracking; the next step starts from the updated slice after reviewed merge and authorization; integration uses child review and acceptance evidence | Tracking walkthrough and actual initial PR hierarchy, followed by slice 03 fixtures |
| AC-6 | Review the overhead baseline and navigation/code-change examples | Amendment separates draft checks from merge CI, bounds execution effort, identifies evidence invalidation and reduces duplicate tracking; adoption remains explicit | Recorded baseline and manual rule walkthrough; later selection/provenance fixtures |

## Boundaries and next review

Guidance approval does not validate future behavior or language tooling. After
adoption, slice 02 investigates candidates one question at a time. Journal events
and approvals for this slice belong to the [parent journal](../journal.md).
