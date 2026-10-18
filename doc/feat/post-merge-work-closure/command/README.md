# Deliver mechanical Work closure

## Purpose

Close explicitly authorized Works on their reviewed open PR and
publish their mechanical repository changes without an agent interpreting and
executing the cleanup procedure each time.

## Goals

- Expose closure through a Make interface defined by lifecycle guidance.
- Apply only the reference updates defined by lifecycle guidance.
- Publish closure on the same PR branch and support separate post-merge cleanup.

## Non-Goals

- Decide whether implementation fulfills criteria or merge an implementation PR.
- Generate semantic dependency prose or modify unrelated working files.
- Change repository settings or bypass hooks, signing, or Git refusals.

## Mechanisms

- Make provides the command interface and owns environment/tool discovery.
- Git and repository PR metadata bind closure to the authorized reviewed head.
- Existing worktree removal commands provide guarded local Git cleanup.

## Acceptance criteria

### **AC-1 TODO** Closure preserves completion and explicit abort decisions

The planned `make work-close ARGS='path/to/README.md ...'` command validates
selected contracts, repository, reviewed open PR head, branch tips, and
reference updates under
[authorized closure guidance](../../../acceptance-tracing.md#authorized-closure).
Session authorization belongs to the maintainer and agent; the command requires
no proof of chat authorization, approval file, or token.

- Selection may include a requested parent and its authorized descendants;
  unrelated or unauthorized Works remain untouched.
- With `TODO` criteria, the command reports them and asks whether to abort the
  remaining outcomes, then exits without repository changes or waiting for
  interactive input.
- The agent relays the question and reruns the same selection with
  `ABORT_REMAINING=true` only after explicit maintainer confirmation;
  cancellation or no answer leaves the repository unchanged.
- Confirmation records the remaining criteria `ABORT` with the reason.
- Each selected Work and its parent/dependency entries close as `DONE` only
  when all its criteria are `DONE`, or as `ABORT` when any criterion is `ABORT`,
  preserving each Work's own result when several are closed together.
- Criterion identities and abort dispositions remain inspectable in committed
  Git history after contract deletion; the command must not rely on same-commit
  edits that are deleted without a retained history entry.
- Work checking and criterion status guidance support `ABORT` as stopped,
  unsatisfied outcomes; the existing `TODO`/`DONE`-only criterion parser
  requires this extension before the command can deliver abort closure. Until
  then, preserve contracts and pause incomplete closure; completed Works may
  use the current Executor, Orchestrator, and Publisher route.
- The planned `make work-close` interface takes only Work README paths in
  `ARGS`, with `ABORT_REMAINING=true` as the separate confirmed operation flag.
- Missing or invalid selection, dirty state, mismatched PR/contracts,
  unexpected tips, unsafe paths, and unresolved or ambiguous reference updates
  refuse publication without inferring approval from completion signals.

### **AC-2 TODO** Repository closure publishes only mechanical changes

The command removes the selected contracts, updates parent/dependent links, and
handles supporting artifacts using the
[Work lifecycle rules](../../../workflow.md#lifecycle), preserving entry titles
and purpose text while removing contract links.
It creates a closure commit containing
only those changes, runs applicable checks and ordinary hooks/signing, and
pushes normally to the same PR branch. It verifies remote publication before
reporting closure publication, without claiming merge or cleanup completion.
Concurrent branch or PR changes cause a bounded refusal with recoverable state
rather than a force push or silent semantic merge. Already-closed input reports
its disposition without duplicate commits or unrelated edits. The resulting
closure head remains subject to full CI and maintainer merge.

### **AC-3 TODO** Git cleanup preserves undelivered work

Only a separate post-merge `make work-cleanup PR=<number>` phase or reinvocation
may remove the associated clean linked worktree and merged local/remote
branches, after verifying merged closure provenance and exact tips using
existing guarded targets. Pushing closure to an open PR never authorizes
cleanup. Cleanup runs from a surviving worktree, never deletes its own executing
worktree, and preserves active dependent branches, unexpected tips,
dirty/untracked work, and uncertain state. Failure reports completed and
remaining operations so a retry cannot repeat publication or lose work.

### **AC-4 TODO** Command behavior is exercised at its real boundary

Disposable repository/remote fixtures exercise actual reference and Git
operations through Make with a controlled PR metadata boundary.

- Open PR cases cover verified selection and reviewed-head boundaries,
  including corrections requiring restoration and renewed session instruction,
  without pretending tools can prove maintainer chat authorization.
- Incomplete-Work cases cover reporting `TODO` criteria before any changes,
  cancellation/no answer preserving all state, and explicit confirmation
  recording criteria and closure entries `ABORT` rather than `DONE`.
- Closure cases cover parent/dependent rewrites, same-branch publication,
  exact-tip races, refusals, publication failures, and retry without duplicate
  closure.
- Final-head CI and maintainer merge remain gates, and cleanup refuses an open
  PR even after successful closure publication.
- Merged cleanup cases preserve dirty/untracked work, dependent branches, and
  unexpected tips, with recoverable partial failure and safe reinvocation.
- Tests do not push to production or claim untested host support.

## Dependencies

- **DONE** Lifecycle guidance: supplies supported
  reference forms; lasting authorization and publication rules are owned by
  [Work acceptance](../../../acceptance-tracing.md#authorized-closure).

## Links

- [Branch cleanup](../../../branch-cleanup.md): existing merged-tip, dependent
  branch, and clean worktree safeguards to preserve.
