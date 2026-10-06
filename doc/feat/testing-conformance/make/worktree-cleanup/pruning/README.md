# Worktree pruning and preview

After removal delivery, migrate missing-expiry preview/apply cases and the
historical-cutoff then now preview/apply sequence. Preserve stale eligibility,
live and locked registrations, branch refs, literal expiry handling, and
read-only preview snapshots through real Git. Use explicit isolated environments
and typed timeout-owning helpers; no sleeps, timing assertions, framework, or
production changes. Include cleaned files in strict Pyrefly and remove the
legacy module only when empty; retain original covers provenance.

- **AC-1 TODO** Given missing expiry, preview and apply refuse with defined
  failure codes before changing files, refs, or registrations.

  Validation: run marked missing-input cases; review exact diagnostics and
  complete relevant before/after snapshots, strict typecheck, and full CI.
- **AC-2 TODO** Given stale, live, and locked worktrees, a historical cutoff
  retains ineligible registrations; now-preview is read-only and now-apply
  prunes only eligible stale registrations while preserving live/locked state
  and all branch refs.

  Validation: run the marked lifecycle case with real Git; independently review
  cutoff/preview/apply observations, literal-input preservation, retained
  regression coverage, strict typecheck, and latest-head full CI.
