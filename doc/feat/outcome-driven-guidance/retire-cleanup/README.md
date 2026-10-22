# Retire the cleanup process

## Purpose

Remove prescribed Work closure and post-merge Git cleanup procedures while
preserving artifacts.

## Goals

- Make completing a Work independent of deleting its contracts or artifacts.
- Leave replacement cleanup design for a later decision.

## Inherited constraints

Apply the [parent constraints](../README.md#inherited-constraints).

## Non-Goals

- Delete existing Work contracts, architecture artifacts, branches, or
  worktrees.
- Implement the pending closure command or replace cleanup with another process.

## Acceptance criteria

### **AC-1 TODO** Completion no longer triggers the current cleanup process

Current guidance and routes no longer prescribe contract deletion, mechanical
closure publication, cleaner dispatch, or post-merge branch/worktree cleanup as
delivery steps. Work/artifact closure means removing retained delivery records;
Git cleanup means removing branches and worktrees. Removing either procedure
does not authorize the other. Completed Works and typed architecture remain
available through parent completion, which gives no automatic deletion
authority. Ordinary Git worktree creation and safe low-level tools may remain
without a required cleanup lifecycle.

### **AC-2 TODO** Pending cleanup plans cannot restore the retired process

The [post-merge closure parent](../../post-merge-work-closure/README.md), its
[command child](../../post-merge-work-closure/command/README.md), and
[adoption child](../../post-merge-work-closure/adoption/README.md) remain
retained records with an explicit superseded disposition: their unfinished
closure-command and cleanup-adoption outcomes are no longer scheduled or
prerequisites for delivery. Their already delivered historical outcomes remain
distinguishable from abandoned plans. Current owners and decision history agree
that replacement design is deferred. No unfinished outcome is marked `DONE`
merely because its plan was retired; any needed status representation follows
the supported format and explicit maintainer authorization.

## Links

- [Work acceptance](../../../acceptance-tracing.md) and
  [Work workflow](../../../workflow.md): current Work/artifact closure rules.
- [Branch cleanup](../../../branch-cleanup.md): current separate Git cleanup
  procedure.
- [Orchestrator guidance](../../../orchestrator.md),
  [contributor guidance](../../../../CONTRIBUTING.md), and
  [task routes](../../../../AGENTS.md): current cleanup dispatch and reading
  routes.

## Additional context

This child is first so subsequent guidance changes do not inherit a requirement
to remove their delivery records. This planning change retains the existing
closure Works unchanged; their disposition is an outcome of this child's later
implementation.
