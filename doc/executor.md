# Executor guidance

Read when acting as executor for an assigned repository change.
The Work README defines the outcome; linked guidance and supporting artifacts
supply context. This file describes execution and return for owner review.

## Execute the assignment

Read the assigned Work and applicable contracts. When no Work contract exists,
use the acceptance criteria supplied in the handoff. Consult ancestor Work
READMEs only when needed. Follow shared setup, branch, engineering, testing,
acceptance, and publication rules at their existing owners; this guidance does
not replace them.
When changing code or tests, apply
[engineering judgment in review](engineering-review.md) alongside the
applicable engineering and testing guidance.
Follow the [routine-choice guidance](workflow.md#scope-and-sizing) for
decisions within the agreed contract.

Keep one coherent outcome moving toward an executable path. When architectural
decomposition is uncertain, use the bounded
[architecture exploration](architecture-exploration.md) route; do not turn
exploration or implementation steps into mandatory Works or agent assignments.
Where it helps expose the outcome early, establish typed composition with real
sequencing and effect ownership, then leave unfinished leaf operations stubbed
and use a thin executable path through the real orchestration. Fake adapters
may supply external effects. These are progression choices within one Work,
not required phases; preserve its contract and review gates throughout.

Before editing, verify that the supplied worktree, branch, and base match the
assignment. Follow the supplied create-or-resume instructions and report a
missing or inconsistent assignment to the owning orchestrator before editing.
Use the assigned isolated worktree and environment; setup is documented in
[contributor guidance](../CONTRIBUTING.md#getting-started).

Make only the approved bounded change. Do not recursively delegate. If the
approved scope or its acceptance criteria are missing or inconsistent, or the
assignment requires work outside that scope, stop before expanding and report
the finding and evidence to the owner. A new split or needed decision pauses
under the
[Work workflow](workflow.md#decisions-and-new-splits).

Before handoff, self-review the exact changed code and tests using
[engineering judgment in review](engineering-review.md). Apply its questions
while implementing too; passing checks do not establish design judgment.

For parent-map updates, follow the executor route in the
[Work workflow](workflow.md#lifecycle).

## Return for review

Return the artifact revision and outcome, unresolved criteria, and material
failures, limitations, or blockers. Point to existing evidence sources needed
for review under [Work acceptance](acceptance-tracing.md#evidence). A completed
return identifies changes awaiting owner review; a blocked return says what
remains and what input or decision is needed. If continuing after an interrupted
session, report the recovered state and which changes and evidence apply to the
current revision. If that state is uncertain, report the uncertainty and wait
for owner steering rather than treating the assignment as complete.

The owning orchestrator independently reviews the artifact and evidence,
coordinates corrections and delivery, and retains publication and maintainer
handoff responsibility. Follow [Pull requests](pull-requests.md#descriptions)
for the executor's concise local result and the owner's publication boundary.
