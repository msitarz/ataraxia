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

### **AC-1 DONE** Completion no longer triggers the current cleanup process

Current guidance and routes no longer prescribe contract deletion, mechanical
closure publication, cleaner dispatch, or post-merge branch/worktree cleanup as
delivery steps. Both procedures are intentionally retired: Work/artifact
closure removes retained delivery records, while Git cleanup removes branches
and worktrees. Cleanup is left to the maintainer manually so its natural
evolution can inform a later process decision. Artifact retention follows the
[parent constraints](../README.md#inherited-constraints), and the maintainer
removes architecture artifacts manually later. No automatic deletion or new
cleanup process replaces the retired procedures. Ordinary Git worktree creation
and safe low-level tools may remain without a required cleanup lifecycle.

### **AC-2 DONE** Pending cleanup plans cannot restore the retired process

The [post-merge closure parent](../../post-merge-work-closure/README.md), its
[command child](../../post-merge-work-closure/command/README.md), and
[adoption child](../../post-merge-work-closure/adoption/README.md) remain
retained records with an explicit superseded disposition: their unfinished
closure-command and cleanup-adoption outcomes are no longer scheduled or
prerequisites for delivery. Their already delivered historical outcomes remain
distinguishable from abandoned plans. Current owners and decision history agree
that replacement design is deferred. No unfinished outcome is marked `DONE`
merely because its plan was retired; the existing `TODO` criterion syntax is
preserved without parser changes.

## Links

- [Work acceptance](../../../acceptance-tracing.md) and
  [Work workflow](../../../workflow.md): current retention rules.
- [Branch cleanup](../../../branch-cleanup.md): notice that the former
  post-merge procedure is retired.
- [Orchestrator guidance](../../../orchestrator.md),
  [contributor guidance](../../../../CONTRIBUTING.md), and
  [task routes](../../../../AGENTS.md): current Work delivery routes.

## Additional context

This child retires prescribed artifact removal and post-merge Git cleanup.
It retains the existing closure Works and marks their unfinished plans as
superseded without changing their historical criterion statuses.
