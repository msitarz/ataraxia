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
Follow the [routine-choice guidance](workflow.md#scope-and-sizing) for
decisions within the agreed contract.

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
