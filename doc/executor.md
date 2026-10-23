# Executor guidance

Read when acting as executor for an assigned repository change. The Work README
defines the outcome; linked guidance and supporting artifacts supply context.
This file owns execution and assignment return duties. A return may provide an
intermediate artifact within an unfinished Work; criterion status and Work
completion follow [Work acceptance](acceptance-tracing.md#criterion-status).

## Execute the assignment

- Read the assigned Work and applicable contracts.
- When no Work contract exists, use the acceptance criteria supplied in the
  handoff.
- Consult ancestor Work READMEs only when needed.
- Follow shared setup, branch, engineering, testing, acceptance, and publication
  rules at their existing owners; this guidance does not replace them.
- When changing code or tests, apply
  [engineering judgment in review](engineering-review.md) alongside the
  applicable engineering and testing guidance.
- Follow the [routine-choice guidance](workflow.md#scope-and-sizing) for
  decisions within the agreed contract.
- For progressive implementation, follow
  [engineering guidance](engineering.md#progressive-implementation),
  [testing guidance](testing.md), and
  [engineering review](engineering-review.md).
- When architectural exploration is needed, follow
  [architecture exploration](architecture-exploration.md).
- Keep implementation within the approved outcome.
- Preserve its contract and review gates.
- Before editing, verify that the supplied worktree, branch, and base match the
  assignment.
- Follow the supplied create-or-resume instructions.
- Report a missing or inconsistent assignment to the owning orchestrator before
  editing.
- Use the assigned isolated worktree and environment.

Setup is documented in
[contributor guidance](../CONTRIBUTING.md#getting-started).

- Make only the approved bounded change.
- Do not recursively delegate.
- If the approved scope or its acceptance criteria are missing or inconsistent,
  or the assignment requires work outside that scope, stop before expanding and
  report the finding and evidence to the owner.

A new split or needed decision pauses under the
[Work workflow](workflow.md#decisions-and-new-splits).

- Before handoff, self-review the exact changed code and tests using
  [engineering judgment in review](engineering-review.md).
- Apply its questions while implementing too.

Passing checks do not establish design judgment.

- When the owning Orchestrator requests corrections, follow its bounded review
  and stopping rules in
  [Orchestrator guidance](orchestrator.md#review-and-return).
- If a correction cannot proceed within the approved outcome, return the
  current revision, concrete evidence, and the decision or help needed instead
  of expanding scope.

For parent-map updates, follow the executor route in the
[Work workflow](workflow.md#lifecycle).

## Assignment return

Use [Orchestrator handoffs](orchestrator.md#roles-and-delegation) for the
assignment's scope, reviewer, and stopping point. Return according to these
rules:

- Return after the assigned scope and applicable subordinate reviews are
  complete.
- Identify the artifact and revision, assigned scope, next reviewer, stopping
  point, unresolved criteria, and material failures, limitations, or blockers.
- For a selected architecture or wiring review, return the completed artifact
  to its named reviewer.
- If that review is the stopping point, wait for it to finish before continuing.
- Sending a return does not authorize continuation past the stopping point.
- If the assigned scope or subordinate review is unfinished, report a blocker
  update rather than a completed return.

Follow [progressive implementation](engineering.md#progressive-implementation)
for optional increments and tests alongside the relevant increment.

## Return for review

- Follow [Work acceptance](acceptance-tracing.md) for criterion status and
  evidence.
- If continuing after an interrupted session, report the recovered state and
  which changes and evidence apply to the current revision.
- If that state is uncertain, report it and wait for owner steering.

The owning orchestrator independently reviews the artifact and evidence,
coordinates corrections and delivery, and retains publication and maintainer
handoff responsibility.

Follow [Pull requests](pull-requests.md#descriptions) for the executor's concise
local result and the owner's publication boundary.
