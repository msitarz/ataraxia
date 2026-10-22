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

- Delete other existing Work contracts, architecture artifacts, branches, or
  worktrees. The maintainer has explicitly authorized deleting only the three
  obsolete post-merge closure contracts named in AC-2.
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

### **AC-2 DONE** Remove the three obsolete closure contracts

The following three obsolete contracts are absent from the current tree:

- `doc/feat/post-merge-work-closure/README.md`
- `doc/feat/post-merge-work-closure/command/README.md`
- `doc/feat/post-merge-work-closure/adoption/README.md`

The lifecycle guidance was delivered; the command and adoption plans were
unfinished and were never implemented. Git history preserves their prior
states. References to the removed contracts are absent from current guidance.
[WDR 30](../../../wdr/0030-retire-prescribed-work-and-git-cleanup.md) records
the cleanup rationale. Work discovery, checks, and criterion parsing are
unchanged.

## Links

- [Work acceptance](../../../acceptance-tracing.md) and
  [Work workflow](../../../workflow.md): current retention rules.
- [Branch cleanup](../../../branch-cleanup.md): notice that the former
  post-merge procedure is retired.
- [Orchestrator guidance](../../../orchestrator.md),
  [contributor guidance](../../../../CONTRIBUTING.md), and
  [task routes](../../../../AGENTS.md): current Work delivery routes.

## Additional context

This child retires prescribed artifact removal and post-merge Git cleanup. Its
AC-2 applies the maintainer's exact exception to the prior retention decision;
it does not authorize broader contract or artifact removal.
