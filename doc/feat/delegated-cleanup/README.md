# Delegated post-merge cleanup

Define and evaluate a distinct `cleaner` role for removing verified merged
Work branches and linked worktrees. Preserve maintainer confirmation, existing
cleanup guardrails, and serialized shared-Git operations. This tests whether
delegation reduces orchestrator cleanup effort; no cost or speed improvement is
assumed.

## Delivery map

- **TODO** [Cleanup role guidance and WDR](guidance/README.md): specify
  operational handoff, verification, safe removal, reporting, and the
  consequential workflow decision.
- **TODO** [Operational trial](trial/README.md): reuse the role for a later
  maintainer-confirmed merge and assess observed outcomes without manufacturing
  destructive cases or claiming a benchmark.

Merge the parent plan before either child. Merge guidance and its WDR before the
trial. Keep cleanup operations serialized with worktree creation and other
shared Git mutations. Existing post-merge rules in
[`doc/branch-cleanup.md`](../../branch-cleanup.md) remain authoritative until
the guidance child is delivered.

## Acceptance

- **AC-1 TODO** Given both child contracts, their sequence and boundaries
  preserve maintainer control and existing cleanup safety while separating role
  guidance from operational evidence.

  Validation: manually review the child outcomes, dependency order, and scope
  against current branch-cleanup, orchestrator, Work, WDR, and PR guidance.
