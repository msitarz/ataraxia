# Worktree cleanup

Keep real Git removal/pruning cases in disposable repositories. Use explicit Git
configuration/environment and timeout-owning typed helpers. Separate unrelated
help assertions; preserve literal paths, dirty/locked/main/submodule refusals,
missing inputs, unknown registrations, expiry, and live/locked pruning.

- **AC-1 TODO** Given removal/pruning actions, only eligible worktrees are
  removed; refusals preserve data, refs, and registrations, and preview is
  read-only.

  Validation: run focused marked cleanup cases and strict typecheck;
  independently review complete before/after snapshots, retained regression
  tests, and full CI.
