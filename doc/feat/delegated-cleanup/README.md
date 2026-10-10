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
- **TODO** [Operational trial](trial/README.md): reuse the role for a later
  maintainer-confirmed merge and assess observed outcomes without manufacturing
  destructive cases or claiming a benchmark.

Merge the parent plan before its trial child. The guidance and WDR are
delivered; the trial can begin after this guidance merges. Keep cleanup
operations serialized with worktree creation and other shared Git mutations. The
post-merge procedure in [`doc/branch-cleanup.md`](../../branch-cleanup.md)
remains authoritative.

## Acceptance

- **AC-1 TODO** Given both child contracts, their sequence and boundaries
  preserve maintainer control and existing cleanup safety while separating role
  guidance from operational evidence.

  Validation: manually review the child outcomes, dependency order, and scope
  against current branch-cleanup, orchestrator, Work, WDR, and PR guidance.
