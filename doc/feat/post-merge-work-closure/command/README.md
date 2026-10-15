# Deliver mechanical Work closure

## Purpose

Close accepted merged Works and publish their mechanical repository changes
without an agent interpreting and executing the cleanup procedure each time.

## Goals

- Expose closure through `make work-close WORK=path/to/README.md PR=number`.
- Apply only the reference updates defined by lifecycle guidance.
- Publish closure and safely clean up the associated Git branch/worktree.

## Non-Goals

- Decide whether implementation fulfills criteria or merge an implementation PR.
- Generate semantic dependency prose or modify unrelated working files.
- Change repository settings or bypass hooks, signing, or Git refusals.

## Mechanisms

- Make provides the command interface and owns environment/tool discovery.
- Git and repository PR metadata bind the contract to the merged delivery.
- Existing worktree removal commands provide guarded local Git cleanup.

## Acceptance criteria

### **AC-1 TODO** Closure is restricted to accepted merged contracts

`make work-close WORK=path/to/README.md PR=number` verifies the repository,
merged PR revision, current master, selected contract, and accepted criteria
before creating closure changes. A requested parent can close its completed
descendants from that merged delivery; unrelated or still-active Works cannot be
included. The command refuses dirty state, incomplete criteria, mismatched
PR/contracts, unsafe paths, unmerged work, and ambiguous references before
publication.

### **AC-2 TODO** Repository closure publishes only mechanical changes

The command removes the selected contracts, updates parent/dependent links using
the lifecycle's canonical rules, and preserves supporting artifacts unless
reviewed removal/promotion is explicit. It creates a closure commit containing
only those changes, runs applicable checks and ordinary hooks/signing, and
pushes normally to master. It verifies remote publication before reporting
success. Concurrent master changes cause a bounded refusal with recoverable
state rather than a force push or silent semantic merge. Already-closed input
reports its disposition without duplicate commits or unrelated edits.

### **AC-3 TODO** Git cleanup preserves undelivered work

Only after verified closure publication does the command remove the associated
clean linked worktree and merged local/remote branches, using the verified tips
and existing guarded targets. It runs from a surviving worktree, never deletes
its own executing worktree, and preserves active dependent branches, unexpected
tips, dirty/untracked work, and uncertain state. Failure reports completed and
remaining operations so a retry cannot repeat publication or lose work.

### **AC-4 TODO** Command behavior is exercised at its real boundary

Disposable repository/remote fixtures establish merged and unmerged cases,
parent/dependent rewrites, refusal paths, publication races/failures, repeat
invocation, and cleanup preservation through Make. Tests exercise our actual
reference and Git operations with a controlled PR metadata boundary, without
pushing to the production remote or claiming untested host support.

## Dependencies

- **TODO** [Lifecycle guidance](../lifecycle/README.md): supplies supported
  reference forms, acceptance/merge preconditions, and publication authority.

## Links

- [Branch cleanup](../../../branch-cleanup.md): existing merged-tip, dependent
  branch, and clean worktree safeguards to preserve.
