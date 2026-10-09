# Review direct leaves on one accumulating branch

After planning guidance, own direct-leaf execution/review at
[orchestrator guidance](../../../orchestrator.md) and the related local commit
sequence at [acceptance tracing](../../../acceptance-tracing.md). A requested
leaf follows its usual Work PR flow. A requested parent assigns its direct
leaves sequentially to the same executor/session in one isolated accumulating
branch/worktree, with an explicit destination, branch and base-ref handoff.
Reconcile the existing per-leaf-worktree wording for this scope without changing
tool behavior or inventing a new role.

Review each complete local artifact/evidence and consolidated corrections before
the next leaf. Within the accumulating requested-parent branch, local acceptance
of a dependency allows its next dependent leaf to proceed without a master
merge. Preserve every leaf's verified retained contract and later cleanup/map
commit pair in order, then complete the parent's own independently reviewed
verification/cleanup pair. Parent owners own maps; the executor applies only
reviewed updates. Reuse valid evidence and track corrections, without publishing
child leaf PRs from a requested-parent run. CI-specific acceptance remains TODO
until observed; unsupported acceptance prevents cleanup and requires tree-wide
steering.

- **AC-1 TODO** Given a requested leaf or direct-leaf parent, guidance selects
  the appropriate isolated execution sequence and retains independently reviewed
  leaf and parent verification/cleanup pairs, allowing locally accepted
  dependencies without premature publication or unsupported DONE.

  Validation: manually walk two sequential leaves, a correction and explicit
  CI-dependent acceptance through owning guidance; inspect maps/history and run
  doc/ac checks. Preserve WDR21's evidence and final-head CI boundaries.
