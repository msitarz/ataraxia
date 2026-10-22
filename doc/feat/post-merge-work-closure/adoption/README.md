# Adopt authorized closure and post-merge cleanup

> **Historical plan, superseded by
> [WDR 30](../../../wdr/0030-retire-prescribed-work-and-git-cleanup.md).** This
> adoption work was not delivered and is no longer scheduled or a delivery
> prerequisite. Its criteria remain `TODO` to distinguish the abandoned plan
> from completed work.

## Purpose

Make the deterministic command the discoverable cleanup route and remove the
replaced cleaner-agent instructions without losing cleanup safeguards.

## Goals

- Route authorized PR closure and separate post-merge Git cleanup to Make.
- Remove cleaner-role instructions replaced by the tool.
- Verify that authorization, closure, corrections, merge, and recovery agree.

## Non-Goals

- Remove implementation review or alter other agent roles.
- Close unrelated live Works as a demonstration.

## Acceptance criteria

### **AC-1 TODO** One operational route preserves the merge boundary

Branch cleanup, orchestrator handoffs, task routing, glossary, Make help, and
contributor guidance route authorized closure to the command and Git cleanup to
its separate post-merge phase or reinvocation.
Cleaner-role guidance and required cleaner dispatch are removed for operations
now owned by the tool. Commands and supported conditions are described at one
owner, without duplicating the procedure across reading routes.

### **AC-2 TODO** Lifecycle and tool compose through correction and recovery

Review of the final guidance and disposable command results confirms a retained
contract can be reviewed, explicitly authorized for selected closure, and closed
on the same PR branch with coherent parent/dependent references. Corrections
after approval restore affected contracts when needed and require refreshed
review and renewed authorization. Full CI passes on the final closure head
before maintainer merge; branch/worktree removal requires verified merged
closure provenance. Required evidence and maintainer acceptance survive, and
failure/retry behavior preserves unpublished changes.
Earlier delivery rules are amended through their decision history rather than
left as conflicting current guidance. Applicable documentation and focused
command checks pass; latest-head CI remains the merge gate.

## Dependencies

- **DONE** Lifecycle guidance: supplies the adopted
  contract and decision.
- **ABORT** [Mechanical closure command](../command/README.md): supplies
  observed command behavior and supported cleanup operations. Superseded by
  WDR 30; unfinished outcomes were not delivered.

## Links

- [Parent Work](../README.md): overall delivery scope.
