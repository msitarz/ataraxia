---
id: F28
kind: feat
status: proposed
stage: relocating-slice-01-delivery
issue: 28
pr: 29
branch: feat/reviewable-workflow
base_branch: feat/parallel_execution
base_revision: "220e3f1f94ca910baee07984c10b483b4499dc6e"
specification_revision: "dd0a9c16665bef9490b0a0d550b8f43767d2eb16"
approved_revision: null
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

Start with [tracking and merge boundaries](spec.md#delivery-tracking-and-merge-boundaries)
and the [branch hierarchy](design.md#how-do-reviewed-changes-reach-the-integration-base).
Slice and step PRs will provide their own review entry points. Approving the
direction does not approve unresolved tool choices or later implementation steps.

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
commits. The next action is to replay the approval/handoff on a slice integration
branch and the template/example on its first step branch, then publish separate
draft PRs. The feat branch contains the proposal and relocation record while
the implementation is reviewed in its child PRs. Iteration 2 has not started.
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
