# Executor guidance

Read when acting as executor for an assigned repository change.
The Work README defines the outcome; linked guidance and supporting artifacts
supply context. This file describes execution and assignment return for owner
review. A completed assignment return may be an intermediate artifact within a
Work; it does not by itself mean the Work is complete.

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

For progressive implementation, follow
[engineering guidance](engineering.md#progressive-implementation),
[testing guidance](testing.md), and
[engineering review](engineering-review.md). When architectural exploration
is needed, follow [architecture exploration](architecture-exploration.md).
Keep implementation within the approved outcome and preserve its contract and
review gates.

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

When the owning Orchestrator requests corrections, follow its bounded review
and stopping rules in
[Orchestrator guidance](orchestrator.md#review-and-return). If a correction
cannot proceed within the approved outcome, return the current revision,
concrete evidence, and the decision or help needed instead of expanding scope.

For parent-map updates, follow the executor route in the
[Work workflow](workflow.md#lifecycle).

## Assignment return

Return when the assigned scope is complete and any reviews assigned beneath it
are complete, so the owner can review the exact result. Identify the artifact
and revision, the assigned scope, the reviewer expected to act next, the
stopping point, unresolved criteria, and material failures, limitations, or
blockers. A return may deliver a Work contract, reviewed typed architecture,
typed wiring, or completed behavior. Tests progress alongside the relevant
increment; the sequence is proportional to the outcome and does not require
every kind of artifact or a separate test stage.

An architecture or wiring review assignment returns its reviewed artifact and
findings to its owner, then waits for that applicable review before
implementation continues. Do not proceed past the named stopping point on the
basis of a sent return alone. A return with unfinished assigned scope or
unfinished subordinate review is a blocker update, not a completed assignment
return.

## Return for review

For a completed Work, follow the Work-level acceptance and evidence rules in
[Work acceptance](acceptance-tracing.md#evidence). Intermediate assignment
returns do not mark Work criteria `DONE` or imply that the Work is complete.
Point to existing evidence sources needed for review. If continuing after an
interrupted session, report the recovered state and which changes and evidence
apply to the current revision. If that state is uncertain, report the
uncertainty and wait for owner steering rather than treating the assignment as
complete.

The owning orchestrator independently reviews the artifact and evidence,
coordinates corrections and delivery, and retains publication and maintainer
handoff responsibility. Follow [Pull requests](pull-requests.md#descriptions)
for the executor's concise local result and the owner's publication boundary.
