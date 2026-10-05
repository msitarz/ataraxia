# Make testing boundaries

Make orchestration should use real Make and a reusable fixture-file fake uv,
with explicit child environments, logs, configurable failures, and timeouts.
Retain real Git for repository effects and real tools for distinct regressions.

The next planning delivery defines bounded leaves for:

- Registering `real_tool` for real uv-managed tool executions, including nested
  pytest; fake-uv and real-Git-only tests remain unmarked. Normal CI runs all.
- Sharing the stub environment and migrating ordinary routing, followed by
  focused verify/CI/setup orchestration coverage.
- Separately preserving worktree creation and cleanup contracts, including
  hostile input, refusal-state preservation, and isolated Git configuration.
- Separately retaining documentation, acceptance-target, and statement-size
  boundary checks in disposable checkouts with real repository configuration.

Marker registration precedes baseline measurement; the shared stub precedes
orchestration migration. Sequence helper edits. Before measurement, declare
matched revisions, prepared offline conditions, duration reporting, three runs
per condition, and handling of failures/skips under
[empirical evaluation guidance](../../../evaluation.md). Compare full-suite and
unmarked selections after cleanup; report observed medians rather than promising
a percentage improvement. Filtering uses scoped `PYTEST_ADDOPTS`; `ARGS` remains
paths-only. Preserve coverage as a prerequisite to interpreting runtime changes.
