# Adopt bounded Hypothesis settings

Own the development dependency in `pyproject.toml`/`uv.lock`, a small typed
`test/conftest.py` settings registration/selection, and narrow property guidance
at [testing](../../../../testing.md). No production API or reusable fixture API
is introduced. Use the official
[settings tutorial](https://hypothesis.readthedocs.io/en/latest/tutorial/settings.html)
and
[fixture health-check context](https://hypothesis.readthedocs.io/en/latest/_modules/hypothesis/_settings.html)
to check the selected compatible version rather than copying upstream internals.

Set 100 examples for in-process properties and deterministic CI generation.
Subprocess properties explicitly use 25 examples and `deadline=None`, retaining
their process timeouts; do not disable in-process deadlines globally. Preserve
normal shrinking/replay support and record selected settings/version. Arrange
mutable/filesystem state inside each generated example with fresh context
managers, not shared function-scoped fixtures or fixture-health suppression.
Keep setup offline-capable after dependency preparation and execution through
existing Make/pytest/CI routes. Do not add a runner or benchmark protocol.

Preserve current folder-wide strict checks and positive/negative expectations;
type changed configuration/helpers precisely. Dependency/setup checks belong
here before pilot consumers. Existing named tests and production code remain
unchanged. Temporary upstream/settings probes may establish adoption once;
review their ownership before cleanup and preserve observed evidence.

- **AC-1 DONE** Given the prepared locked development environment, normal test
  routes load bounded in-process and deterministic CI settings, permit the
  explicit subprocess override without losing timeouts, and retain isolation
  health checks and precise folder-wide typing.

  Validation: inspect dependency/lock compatibility and owned guidance; exercise
  small disposable settings/plugin probes for normal and CI selection plus the
  subprocess override, run existing named selections and strict type checks,
  then doc/ac checks. Record actual versions/results and unrun limitations.
