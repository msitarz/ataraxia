---
id: F28
kind: feat
status: in progress
stage: awaiting-template-review
issue: 28
pr: 29
branch: feat/reviewable-workflow
base_branch: feat/parallel_execution
base_revision: "220e3f1f94ca910baee07984c10b483b4499dc6e"
specification_revision: "dd0a9c16665bef9490b0a0d550b8f43767d2eb16"
approved_revision: null
review_base_revision: "9231d7164ec41835872bbd594b4e2b3770fbb1ce"
review_revision: "1eb8c19231971586a6baa447fa9b0d1ab84f5797"
---

# Small reviewed iterations

Give the maintainer frequent opportunities to understand changes and steer the
project. Each iteration presents one concrete artifact designed for review in
under five minutes. Discussion can take longer; the agent waits for explicit
approval before the next dependent iteration.

The maintainer adopted the issue/branch/PR hierarchy for this feat and authorized
relocating slice 01's first iteration to child review branches. Shared workflow
guidance is still being delivered under the
[current workflow](../../feat-workflow.md); this explicit instruction governs
the relocation. Tool choices, later iterations and parallel reversal await their
own decisions.

## Review entry point

Review the [candidate artifact template](../../feat-workflow.md#review-artifact-template)
and [worked discovery example](journal.md#j-14-deliver-the-review-template-and-example)
as `F28-01:STEP-1`, tracked in
[issue #32](https://github.com/msitarz/ataraxia/issues/32) and
[draft step PR #33](https://github.com/msitarz/ataraxia/pull/33).
The review range is `9231d7164ec41835872bbd594b4e2b3770fbb1ce` to
`1eb8c19231971586a6baa447fa9b0d1ab84f5797`, also recorded in frontmatter.
It contains the template/example and necessary step tracking; later publication
metadata does not change those artifacts. The [slice integration PR #31](https://github.com/msitarz/ataraxia/pull/31)
remains draft pending delivery steps and full acceptance evidence.
The adopted [tracking contract](spec.md#delivery-tracking-and-merge-boundaries)
and [branch hierarchy](design.md#how-do-reviewed-changes-reach-the-integration-base)
provide context. Approving the direction does not approve unresolved tool choices
or later implementation steps.

| Document | Authoritative content | Read when |
| --- | --- | --- |
| [Spec](spec.md) | Overall scope, observable contracts, acceptance criteria | Defining or reviewing the direction |
| [Design](design.md) | Proposed document ownership, checker composition, dependencies | Assessing how the direction fits together |
| [Journal](journal.md) | Consequential changes, investigations, approvals, evidence | Resuming work or examining the basis of a decision |
| Delivery slices below | Local acceptance criteria and small delivery steps | Reviewing or executing that outcome |

## Delivery order

| Slice | Reviewable outcome | Depends on |
| --- | --- | --- |
| [01: Review loop](slices/01-review-loop.md) | Workflow guidance, artifact format, document ownership | Direction approval |
| [02: Tool investigations](slices/02-tool-investigations.md) | Reproducible findings and proposed tool choices | 01 |
| [03: Documentation checks](slices/03-documentation-checks.md) | Hygiene, schemas, graph and revision checks in CI | Relevant choices from 02 |
| [04: Acceptance evidence](slices/04-acceptance-evidence.md) | Plain pytest traceability and explicit non-pytest evidence | 01, relevant choices from 02 and 03 |
| [05: Language checks](slices/05-language-checks.md) | Evaluated STE profile and a scoped pilot, or a recorded deferral | STE findings from 02; checker entry point from 03 |
| [06: Parallel evaluation](slices/06-parallel-evaluation.md) | Manually evaluated reversal and replay under the adopted workflow | 01, 03, 04; disposition of 05 |

Each row contains several iterations. It is not a five-minute review promise for
the whole slice. Tool investigations may change the proposed implementation;
the changed contract or design returns for review before affected work proceeds.

## Current handoff

Defining and executor roles share the
[conversation in J-15](journal.md#j-15-relocate-delivery-to-child-prs).
J-15 records the instruction and authorized reversal of the three slice 01
commits. [J-16](journal.md#j-16-approve-relocated-first-step) records the current
scope at the amended revision; J-13 is preserved as historical approval evidence.
Slice 01's branch and tracking belong to its
[frontmatter](slices/01-review-loop.md), including the registered `STEP-1`.
[J-17](journal.md#j-17-replay-the-template-on-its-step-branch) records the replay;
[J-18](journal.md#j-18-clarify-visual-review-options) records the requested visual
note correction and its checks. The next action is maintainer review of the template/example
in the step PR to the slice. Corrections reuse that step; dependent continuation
waits for approval and reviewed merge. The slice integration PR stays draft
pending its children and full acceptance evidence. Iteration 2 has not started.
Overall specification approval remains pending; there is no independent session
review. Original commits and their evidence remain in Git history.
The [journal](journal.md) owns drafting and validation evidence.
The [visual companion format is accepted](journal.md#j-10-accept-the-visual-review-format);
overall specification review remains pending.
The candidate contracts, design, and delivery slices are committed at the
frontmatter's `specification_revision`; subsequent publication metadata does not
approve or implement them.

[Issue #28](https://github.com/msitarz/ataraxia/issues/28) tracks the eventual
implemented workflow and evaluation. The maintainer requested this stacked base
to retain the familiar parallel implementation for a later controlled replay.
The existing [parallel PR #24](https://github.com/msitarz/ataraxia/pull/24) has its
own pending reviews; this proposal does not resolve them.
The proposal is published in [draft PR #29](https://github.com/msitarz/ataraxia/pull/29).
