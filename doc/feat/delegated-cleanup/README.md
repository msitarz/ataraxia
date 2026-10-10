# Delegated post-merge cleanup

Define and evaluate a distinct `cleaner` role for removing verified merged
Work branches and linked worktrees. Preserve maintainer confirmation, existing
cleanup guardrails, and serialized shared-Git operations. This tests whether
delegation reduces orchestrator cleanup effort; no cost or speed improvement is
assumed.

## Delivery map

- **DONE** Cleanup role guidance and WDR: the cleaner's operational handoff,
  verification and reporting are defined in branch-cleanup and orchestrator
  guidance, with the rationale recorded in WDR 18.
- **DONE** Operational trial: the #271 cleanup was properly scoped and
  preserved unrelated work, but a remote-tracking ref was read during fetch and
  initially reported as a verified remote tip. The report was clarified; no
  live remote tip was verified and no remote deletion occurred. No cost or
  speed claim is made.

The guidance, WDR, and operational assessment are delivered. Keep cleanup
operations serialized with worktree creation and other shared Git mutations.
The post-merge procedure in
[`doc/branch-cleanup.md`](../../branch-cleanup.md) remains authoritative.

## Acceptance

- **AC-1 TODO** Given both child contracts, their sequence and boundaries
  preserve maintainer control and existing cleanup safety while separating role
  guidance from operational evidence.

  Validation: manually review the child outcomes, dependency order, and scope
  against current branch-cleanup, orchestrator, Work, WDR, and PR guidance.
