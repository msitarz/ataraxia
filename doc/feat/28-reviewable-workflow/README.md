---
id: F28
kind: feat
status: in progress
stage: awaiting-continuation-review
issue: 28
pr: 29
branch: feat/reviewable-workflow
base_branch: feat/parallel_execution
base_revision: "220e3f1f94ca910baee07984c10b483b4499dc6e"
specification_revision: "dd0a9c16665bef9490b0a0d550b8f43767d2eb16"
approved_revision: null
review_base_revision: "588cde5ba881b6e20d1dfc0d558ae710e3b6d264"
review_revision: "a7cf2de390e1ea343f54b9701c0f9bdc6b248d22"
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

Review [delivery branches and review gates](../../feat-workflow.md#delivery-branches-and-review-gates),
[material-change handling](../../feat-workflow.md#execute-the-approved-scope),
and the [boundary walkthrough](journal.md#boundary-walkthrough) as
`F28-01:STEP-2`, tracked in [issue #34](https://github.com/msitarz/ataraxia/issues/34).
The review range is `588cde5ba881b6e20d1dfc0d558ae710e3b6d264` to
`a7cf2de390e1ea343f54b9701c0f9bdc6b248d22`, also recorded in frontmatter.
Use the step PR for this guidance and its examples. Later publication metadata
only identifies the review target. Initial review estimate: four minutes.

[Step 1 PR #33](https://github.com/msitarz/ataraxia/pull/33) is merged into the slice.
[Slice integration PR #31](https://github.com/msitarz/ataraxia/pull/31) remains draft
pending its remaining steps and full acceptance evidence. The
[tracking contract](spec.md#delivery-tracking-and-merge-boundaries) and
[branch hierarchy](design.md#how-do-reviewed-changes-reach-the-integration-base)
provide context. Tool choices and later steps await their own decisions.

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

[J-19](journal.md#j-19-authorize-continuation-after-step-1-merge) records the
verified step 1 merge and explicit continuation instruction at the candidate
contract revision. [J-20](journal.md#j-20-deliver-continuation-and-branch-gates)
records step 2's guidance, boundary cases and checks. Slice and step tracking
belong to [slice 01's frontmatter](slices/01-review-loop.md).

The next action is maintainer review of step 2. Corrections reuse that step's PR;
step 3's package template and ownership routes have not started. The slice stays
in progress pending its remaining outcomes and acceptance evidence. The defining
and executor roles share the journal's native conversation; there is no
independent session review. Overall specification approval remains pending.

The [journal](journal.md) owns consequential history and validation evidence.
The candidate contracts, design and delivery slices are committed at the
frontmatter's `specification_revision`; publication metadata does not approve
them or authorize further implementation. The
[visual companion format is accepted](journal.md#j-10-accept-the-visual-review-format).

[Issue #28](https://github.com/msitarz/ataraxia/issues/28) tracks the eventual
implemented workflow and evaluation. The maintainer requested this stacked base
to retain the familiar parallel implementation for a later controlled replay.
The existing [parallel PR #24](https://github.com/msitarz/ataraxia/pull/24) has its
own pending reviews; this proposal does not resolve them.
The proposal is published in [draft PR #29](https://github.com/msitarz/ataraxia/pull/29).
