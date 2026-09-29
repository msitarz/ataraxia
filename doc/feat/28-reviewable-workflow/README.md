---
id: F28
kind: feat
status: proposed
stage: awaiting-specification-review
issue: 28
pr: 29
branch: feat/reviewable-workflow
base_branch: feat/parallel_execution
base_revision: "220e3f1f94ca910baee07984c10b483b4499dc6e"
specification_revision: "0270014fcade2b2c60b1e5563dfb8557eabb7653"
approved_revision: null
---

# Small reviewed iterations

Give the maintainer frequent opportunities to understand changes and steer the
project. Each iteration presents one concrete artifact designed for review in
under five minutes. Discussion can take longer; the agent waits for explicit
approval before the next dependent iteration.

This is a proposal using the proposed file layout. The
[current workflow](../../feat-workflow.md) still governs delivery. No future
implementation, tool selection, or reversal of parallel execution is approved
by publication of this package.

## Review entry point

Start with the [six principles and overall acceptance criteria](spec.md).
Then review one delivery slice at a time. Approving the direction does not
approve unresolved tool choices or every later implementation step.

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

Defining session: [F28:S1](journal.md#j-8-journal-identity-and-session-registration).
No executor session has started.
The next action is manual specification review, beginning with the six principles.
There is no approved specification revision and no independent session review.
The [journal](journal.md) owns drafting and validation evidence.
The candidate contracts, design, and delivery slices are committed at the
frontmatter's `specification_revision`; subsequent publication metadata does not
approve or implement them.

[Issue #28](https://github.com/msitarz/ataraxia/issues/28) tracks the eventual
implemented workflow and evaluation. The maintainer requested this stacked base
to retain the familiar parallel implementation for a later controlled replay.
The existing [parallel PR #24](https://github.com/msitarz/ataraxia/pull/24) has its
own pending reviews; this proposal does not resolve them.
The proposal is published in [draft PR #29](https://github.com/msitarz/ataraxia/pull/29).
