# Executor guidance and handoffs

Make executor obligations directly discoverable and bounded handoffs complete:
one documentation outcome for a maintainer review of about five minutes.

At verified baseline `e996cebe004c673d8fe02ed325fb9a7ecf942413`,
[AGENTS.md](../../../../../AGENTS.md) routes only orchestrators to
[orchestrator guidance](../../../../orchestrator.md), which also contains
executor obligations. Assignment context already includes task, steering,
workspace, branch, base, and creation command;
[CONTRIBUTING.md](../../../../../CONTRIBUTING.md#work-branches-review-and-merge)
requires executors to verify the assignment and report inconsistencies. The
remaining gap is role discovery and a concise, complete handoff boundary.

Proposed after: extract executor-facing instructions about what to do, stop,
and report into `doc/executor.md`, with an executor trigger and direct AGENTS
route. Keep assignment preparation, coordination, recovery decisions,
independent review, and onward delivery in orchestrator guidance, linking to
the executor owner. Preserve definer discovery and requirements at existing
owners; do not create a definer owner or copy executor rules into its guidance.

Update the [documentation ownership](../../../../README.md) and
[Executor glossary route](../../../../ubiquitous-language.md). Review related
CONTRIBUTING, workflow, and PR routes; change links or duplicated instructions
only where extraction requires it. Shared engineering, testing, acceptance,
setup/branch, and publication rules remain at their existing owners.

Strengthen orchestrator assignment guidance with a content checklist:

- Task: Work path, requested action, and only missing steering.
- Workspace: destination path, branch, assigned base, create versus resume,
  and the existing creation/setup route when applicable.
- Authority and stopping point: approved scope, gap reporting, and owner review
  before marking criteria DONE or removing the contract.
- Return: follow the executor owner for artifact revision, outcome, evidence,
  commands and unrun checks, unresolved criteria, blockers, and recovered state;
  identify changes awaiting review or needed steering.

The checklist is not a rigid message template. The Work and linked contracts
own acceptance; the handoff supplies execution context. Preserve unchanged
[orchestration](../../../../orchestrator.md),
[acceptance](../../../../acceptance-tracing.md), and
[publication](../../../../pull-requests.md) responsibilities and gates,
including the requested Work owner's continuation to maintainer PR handoff.
No model/delegation change, new tool, required evidence journal, empirical
behavior claim, or live-trial execution is included. This clarifies accepted
responsibilities; no new WDR is expected. Report any consequential policy gap
before expanding scope under
[Work workflow](../../../../workflow.md#decisions-and-new-splits).

## Acceptance

- **AC-1 DONE** AGENTS routes executors directly to their focused owner;
  ownership, glossary, and shared-guidance routes agree without duplication.
  Validation: manually walk executor startup from AGENTS through affected
  routes, checking reading triggers and authoritative owners.
- **AC-2 DONE** Extraction preserves executor obligations, definer discovery
  and requirements, and orchestrator responsibilities and existing gates.
  Validation: independently compare changed guidance and surrounding sections
  against the verified baseline and linked contracts; trace each moved
  obligation and distinguish executor actions from owner decisions.
- **AC-3 DONE** Handoffs supply the four context groups, a bounded reviewable
  return, and onward owner delivery without duplicating Work acceptance.
  Validation: manually walk a fresh requested leaf, the next accumulating leaf,
  a missing/inconsistent assignment, and an interrupted return/recovery; check
  create/resume base, scope-gap stops, validation before owner review, and owner
  review before DONE/cleanup, completed or blocked returns, and owner steering.
  These are guidance walkthroughs, not observed agent behavior or a live trial.

Run `make doc-format`, `make doc-check`, and `make ac-check` for this README.
Mechanical checks validate documentation and declarations; manual outcomes
require independent review before criteria become `DONE`.
