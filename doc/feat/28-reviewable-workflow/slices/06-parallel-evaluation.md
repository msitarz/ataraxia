---
id: F28-06
kind: slice
parent: F28
status: proposed
approved_revision: null
---

# Evaluate the workflow by replaying parallel execution

## Outcome and prerequisites

After workflow adoption, let the maintainer manually evaluate frequent, small
reviews on an understood problem. Preserve the existing
[parallel slice](../../parallel-execution.md), approved contracts, implementation
and correction references, and historical evidence. Prepare a reviewed reversal
plan, then replay the behavior through the new workflow. This proposal performs
neither reversal nor replay.

Baseline specification: `8442140f0fbbf85a204fd6e15118111af3866a51`.
Corrected implementation: `a421c16`; handoff/base snapshot: `220e3f1`.
Keep [ADR 18](../../../adr/0018-supervise-process-workers-for-shard-timeouts.md),
its [ADR 6](../../../adr/0006-massive-parallelism-via-sharding.md) relationship,
and [ADR 17](../../../adr/0017-enforce-module-dependencies-with-tach.md) constraints.
Accepted decisions do not imply that their implementation currently exists.

## Proposed iterations

| Step | Concrete artifact and decision | Verification and proposed checkers |
| --- | --- | --- |
| 1 | A retained-reference manifest, mapped acceptance rows and exact reversal dependency plan; review what will be removed and preserved | Git reachability/history checks, rumdl/metadata/traceability checks, existing contracts and approved revision comparison |
| 2 | Approved reversal in small coherent commits, with accurately updated current architecture/usage; review the restored baseline | Targeted behavior/type/Tach/package checks, docs ownership/history checks and `make ci`; adopted workflow/tooling remains usable |
| 3 | Small contract/design and preparatory-refactor artifacts for replay; review one boundary at a time | Approved contract diff, semantic/type/module review, rumdl/schema checks, scoped acceptance mapping and adopted language checks |
| 4 | Replay increments, each with tests, structural review, checked commit and explicit continuation approval | Focused unit/real-spawn/CLI evidence and adopted docs/trace/language checks per increment; full `make ci` at slice publication |
| 5 | Comparison and workflow evaluation report; review whether to retain or revise the workflow | All parallel acceptance evidence, sample comparison, original regressions, revision/approval consistency and maintainer feedback |

Before reversal, identify exact implementation, test, and caller changes rather
than revert everything since `master`. Use new commits, preserving shared history
and the adopted workflow. Update current architecture truthfully while retaining
historical specification/evidence and accepted rationale. The reversal itself
needs manual approval of its exact plan and artifact.

Step 4 is a sequence of small iterations, not permission for a supervisor-sized
commit. Suggested boundaries are precise outcome types, sequential continuation,
diagnostic fidelity, output saving, worker startup/ownership, isolated channels,
deadline decisions, worker replacement, shutdown, and CLI exposure. Combine or
split only when each reviewed increment remains coherent and verifiable. Plan
explicit dependencies and available test seams before committing partial work.

Preserve the full exception-group and timely-receipt regression cases as reference
behavior. They fixed implementation defects under the original contracts.
Do not automatically turn every old bug fix into a new requirement, or copy old
passing evidence as validation of the new implementation.

## Acceptance criteria

| ID | Preconditions and action | Observable outcome | Verified by |
| --- | --- | --- | --- |
| AC-1 | Prepare and review the reversal | Durable refs and original contracts remain reachable; explicit scope preserves adopted workflow and shared history | Manifest/history checks and manual approval |
| AC-2 | Execute the approved reversal | Restored baseline passes relevant checks; architecture describes current code; historical decisions/evidence remain distinguishable | Behavior/type/Tach/package checks, docs checks and `make ci` |
| AC-3 | Replay each increment | Actual diff/evidence is exposed and discussed; dependent continuation waits for explicit revision-scoped approval | Journal/revision checks and manual evaluation |
| AC-4 | Compare completed replay with intended parallel behavior | Original acceptance examples and both P2 regressions pass with fresh evidence; intentional changes receive renewed review | Unit, real-spawn, CLI, type and installed-wheel evidence |
| AC-5 | Review the evaluation report | Maintainer can identify understandable versus oversized artifacts, steering opportunities, defects/debt and workflow costs, and decide follow-up changes | Recorded manual observations and decision |

## Evaluation record

Record rough initial review effort, whether the maintainer understood the actual
change, questions/revisions, direction changes, premature continuation attempts,
and documentation/tool overhead. Report failures and deferred review honestly.
No automated timer, line budget, or checker can certify understanding. Keep the
report small, link representative artifacts, and use the [journal](../journal.md)
for consequential findings. A disappointing evaluation is useful evidence;
automatic approval or a required positive verdict would defeat the experiment.
