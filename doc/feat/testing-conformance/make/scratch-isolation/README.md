# Isolate sandbox process scratch

The
[stopped attempt](../matched-measurements.md#final-condition-stopped-comparison-inconclusive)
observed six snapshots changing at `tmp/xcrun_db`. `make_sandbox` currently puts
HOME/TMPDIR inside its repository; `files_under` observes all non-Git files.
Move per-sandbox home and scratch outside the observed repository, still within
its disposable arrangement. Fix this owning boundary without filename
exclusions, weaker snapshots, a generic framework, or production/policy changes.

Preserve explicit child environments, timeouts, repository files, refs and
registrations. Snapshot the repository before a real Make action whose designed
external-process boundary writes home/scratch during execution. This
deterministic regression must fail the old inside-repository arrangement on
every host. Assert home/scratch are outside the observed repository and retain
legitimate similarly named repository files, proving isolation without filename
filters. Use precise types and strictly include changed/new helpers or named
executable fixtures under [testing guidance](../../../../testing.md). Merge
before the
[renewed Evaluation](../renewed-final/README.md).

- **AC-1 TODO** Given a complete repository snapshot before execution and
  process home/scratch outside that repository, writes during a real Make
  action preserve repository files including similarly named legitimate data,
  refs and worktree registrations; the regression detects the old arrangement
  and removal/pruning retain their promises.

  Validation: run criterion-marked regression and removal/pruning cases on the
  affected macOS host through Make; review external home/scratch containment and
  unchanged snapshot strength; run strict typing, lint/format, ac/doc checks and
  latest-head full CI. Preserve existing regression coverage and provenance.
