---
id: F28
kind: feat
status: in progress
stage: awaiting-structural-review
issue: 28
pr: 29
branch: feat/reviewable-workflow
base_branch: feat/parallel_execution
base_revision: "220e3f1f94ca910baee07984c10b483b4499dc6e"
specification_revision: "5d081802630fce38dbaeee3501665ab15636cc34"
approved_revision: null
review_base_revision: "004a6ba66d7422284d071a00a5bfa01f3cbd1f93"
review_revision: null
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

Review the [structural review rule](../../engineering.md#structural-review),
[delivery gate](../../feat-workflow.md#stepwise-changes-and-commits), and
[two-case walkthrough](journal.md#j-27-deliver-structural-review-guidance) and
[base-type correction](journal.md#j-28-clarify-shared-base-types)
as `F28-01:STEP-4`, tracked in
[issue #42](https://github.com/msitarz/ataraxia/issues/42) and
[draft PR #43](https://github.com/msitarz/ataraxia/pull/43).
The step PR will identify its review head against slice merge
`36edc546d33f63c130c930b65884c21f56fd3ec0`. Initial review estimate: four minutes
for the two owner changes and walkthrough; actual feedback is pending.

Step PRs [#33](https://github.com/msitarz/ataraxia/pull/33),
[#35](https://github.com/msitarz/ataraxia/pull/35),
[#37](https://github.com/msitarz/ataraxia/pull/37), and
[#39](https://github.com/msitarz/ataraxia/pull/39), and
[#41](https://github.com/msitarz/ataraxia/pull/41) are merged into the slice.
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

[J-26](journal.md#j-26-authorize-structural-review-guidance) records authorization
after PR #41 merged. [J-27](journal.md#j-27-deliver-structural-review-guidance)
records the rule and walkthrough. Step tracking belongs to
[slice 01](slices/01-review-loop.md). The defining and executor roles share this native
conversation; no independent review is claimed.

The [journal](journal.md) owns consequential history and validation evidence.
The step PR identifies the candidate contracts and design revision; publication
metadata does not approve them or authorize further implementation. The
[visual companion format is accepted](journal.md#j-10-accept-the-visual-review-format).

[Issue #28](https://github.com/msitarz/ataraxia/issues/28) tracks the eventual
implemented workflow and evaluation. The maintainer requested this stacked base
to retain the familiar parallel implementation for a later controlled replay.
The existing [parallel PR #24](https://github.com/msitarz/ataraxia/pull/24) has its
own pending reviews; this proposal does not resolve them.
The proposal is published in [draft PR #29](https://github.com/msitarz/ataraxia/pull/29).
