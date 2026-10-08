# Cleanup role operational trial

After the guidance child merges, reuse the same cleaner agent for a subsequent
maintainer-confirmed Work PR merge. Assess the actual handoff, reported object
comparisons and state checks, removals, blockers, and orchestrator assessment.
Use real occurrences only; do not create artificial destructive cases, add a
logging framework, or claim a benchmark or measured cost reduction.

The earlier #199 cleanup pilot is seed context, not this trial's result: the
first attempt stopped because the merge commit had not been fetched; after
correction round 1 fetched before comparisons, the reviewed and merge trees
matched, dependency and clean-state checks passed, and master plus the named
worktree and branch were cleaned up. Track this role's correction rounds
separately from executor correction counts. Preserve maintainer confirmation,
merge authority, and full-CI gates for the documentation delivery.

- **AC-1 TODO** Given a later confirmed merge handled under the adopted
  guidance, an independent report review establishes whether object and state
  checks were correct, cleanup was properly scoped, and actual blockers were
  reported without weakening existing guardrails.

  Validation: manually review the handoff and cleanup report against observed
  repository state and the adopted guidance; report unavailable occurrences
  or unverified claims without simulating destructive states.
