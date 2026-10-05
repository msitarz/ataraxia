# Real-tool selection

Register strict pytest marker `real_tool`; classify real uv-managed tool runs
in markdown, acceptance-target, and size tests, including nested pytest. Keep
fake-uv and real-Git-only cases unmarked. Change only marker registration and
classification; no fixture cleanup or legacy annotation migration.

- **AC-1 TODO** Given full and filtered collection, only real uv-managed
  executions are excluded by `not real_tool`, while normal Make/CI selection
  includes both.

  Validation: review classification against execution helpers; use Make test
  collection via scoped PYTEST_ADDOPTS for full and filtered selections, then
  run both.
