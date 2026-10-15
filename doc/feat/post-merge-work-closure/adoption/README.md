# Adopt mechanical post-merge cleanup

## Purpose

Make the deterministic command the discoverable cleanup route and remove the
replaced cleaner-agent instructions without losing cleanup safeguards.

## Goals

- Route post-merge closure and Git cleanup to the delivered Make command.
- Remove cleaner-role instructions replaced by the tool.
- Verify that correction, merge, closure, and recovery guidance agree.

## Non-Goals

- Remove implementation review or alter other agent roles.
- Close unrelated live Works as a demonstration.

## Acceptance criteria

### **AC-1 TODO** One post-merge operational route

Branch cleanup, orchestrator handoffs, task routing, glossary, Make help, and
contributor guidance route mechanical closure and Git cleanup to the command.
Cleaner-role guidance and required cleaner dispatch are removed for operations
now owned by the tool. Commands and supported conditions are described at one
owner, without duplicating the procedure across reading routes.

### **AC-2 TODO** Lifecycle and tool compose through correction and recovery

Review of the final guidance and disposable command results confirms a retained
contract can be corrected and merged, then closed with coherent parent/dependent
references before branch/worktree removal. Required evidence and maintainer
acceptance survive, and failure/retry behavior preserves unpublished changes.
Earlier delivery rules are amended through their decision history rather than
left as conflicting current guidance. Applicable documentation and focused
command checks pass; latest-head CI remains the merge gate.

## Dependencies

- **TODO** [Lifecycle guidance](../lifecycle/README.md): supplies the adopted
  contract and decision.
- **TODO** [Mechanical closure command](../command/README.md): supplies observed
  command behavior and supported cleanup operations.

## Links

- [Parent Work](../README.md): overall delivery scope.
