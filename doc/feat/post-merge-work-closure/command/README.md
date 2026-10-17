# Deliver mechanical Work closure

## Purpose

Close explicitly authorized completed Works on their reviewed open PR and
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

### **AC-1 TODO** Closure is restricted to explicitly authorized completed contracts

The Make command verifies the selected completed contracts, repository, reviewed
open PR head, branch tips, and explicit authorization under
[lifecycle AC-1](../lifecycle/README.md#ac-1-done-one-lifecycle-retains-contracts-until-authorized-closure)
before creating closure changes.

- Selection may include a requested parent and its authorized completed
  descendants; unrelated, incomplete, or unauthorized Works remain untouched.
- Missing or stale authorization, dirty state, mismatched PR/contracts,
  unexpected tips, unsafe paths, and unresolved or ambiguous reference updates
  refuse publication without inferring approval from completion signals.

### **AC-2 TODO** Repository closure publishes only mechanical changes

The command removes the selected contracts, updates parent/dependent links, and
handles supporting artifacts using the lifecycle's canonical rules.
It creates a closure commit containing
only those changes, runs applicable checks and ordinary hooks/signing, and
pushes normally to the same PR branch. It verifies remote publication before
reporting closure publication, without claiming merge or cleanup completion.
Concurrent branch or PR changes cause a bounded refusal with recoverable state
rather than a force push or silent semantic merge. Already-closed input reports
its disposition without duplicate commits or unrelated edits. The resulting
closure head remains subject to full CI and maintainer merge.

### **AC-3 TODO** Git cleanup preserves undelivered work

Only a separate post-merge phase or reinvocation may remove the associated clean
linked worktree and merged local/remote branches, after verifying merged closure
provenance and exact tips using existing guarded targets. Pushing closure to an
open PR never authorizes cleanup. Cleanup runs from a surviving worktree, never
deletes its own executing worktree, and preserves active dependent branches,
unexpected tips, dirty/untracked work, and uncertain state. Failure reports
completed and remaining operations so a retry cannot repeat publication or lose
work.

### **AC-4 TODO** Command behavior is exercised at its real boundary

Disposable repository/remote fixtures exercise actual reference and Git
operations through Make with a controlled PR metadata boundary.

- Open PR cases cover absent, valid, and stale closure authorization, including
  corrections requiring restoration and renewed instruction.
- Closure cases cover parent/dependent rewrites, same-branch publication,
  exact-tip races, refusals, publication failures, and retry without duplicate
  closure.
- Final-head CI and maintainer merge remain gates, and cleanup refuses an open
  PR even after successful closure publication.
- Merged cleanup cases preserve dirty/untracked work, dependent branches, and
  unexpected tips, with recoverable partial failure and safe reinvocation.
- Tests do not push to production or claim untested host support.

## Dependencies

- **TODO** [Lifecycle guidance](../lifecycle/README.md): supplies supported
  reference forms, Make interface, authorization boundaries, and publication
  authority.

## Links

- [Branch cleanup](../../../branch-cleanup.md): existing merged-tip, dependent
  branch, and clean worktree safeguards to preserve.
