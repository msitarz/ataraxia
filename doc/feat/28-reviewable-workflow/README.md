---
id: F28
kind: feat
status: in progress
stage: awaiting-iteration-review
issue: 28
pr: 29
branch: feat/reviewable-workflow
base_branch: feat/parallel_execution
base_revision: "220e3f1f94ca910baee07984c10b483b4499dc6e"
specification_revision: "406d2e61356a05b665af6b7aba5c1d25083a57bd"
approved_revision: null
review_base_revision: "6d1a864bad92ac439bbd1f70fe98ba1699e15abe"
review_revision: "efe5d17d06c5b1cd02bba593319ba92eb2b0449e"
---

# Small reviewed iterations

Give the maintainer frequent opportunities to understand changes and steer the
project. Each iteration presents one concrete artifact designed for review in
under five minutes. Discussion can take longer; the agent waits for explicit
approval before the next dependent iteration.

This package has begun scoped delivery under the
[current workflow](../../feat-workflow.md). The maintainer authorized slice 01's
first iteration; the [handoff](#current-handoff) identifies its approval and
limits. Tool choices, later iterations, and parallel reversal remain proposed.

## Review entry point

For slice 01's first iteration, review the
[candidate template](../../feat-workflow.md#review-artifact-template) and
[worked discovery example](journal.md#j-14-deliver-the-review-template-and-example).
The frontmatter's `review_base_revision` and `review_revision` identify the
comparison in Magit or an editor/IDE, including the approval and handoff changes.
The [overall specification](spec.md) retains the larger direction; unresolved
tool choices and later implementation steps have their own review boundaries.

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
[conversation recorded in J-13](journal.md#j-13-approve-slice-01-iteration-1).
There is no independent session review. The maintainer authorized
[slice 01](slices/01-review-loop.md)'s first iteration at the candidate revision
named in its frontmatter; J-13 owns the instruction and exact scope.
The current action is manual review of the delivered template and example at
`review_revision`. [J-14](journal.md#j-14-deliver-the-review-template-and-example)
owns execution and check evidence; maintainer feedback is pending. If accepted,
the proposed next outcome is iteration 2's continuation and material-change
guidance. That iteration has not started. Overall specification approval remains pending;
the overview's `approved_revision` remains null.
The [journal](journal.md) owns approval, execution and validation evidence.
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
