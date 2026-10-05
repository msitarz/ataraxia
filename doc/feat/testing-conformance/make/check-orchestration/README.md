# Check orchestration

Depends on delivered stub helper. Move verify/CI/setup/package routing cases
from `test_makefile.py` into a focused typed module using that helper. Separate
offline flags, preparation allocation, required ordering, full-selector
ignoring, read-only documentation parity, and failure propagation; avoid
incidental logs.

- **AC-1 TODO** Given verify/CI/setup targets and injected failures, promised
  commands and flags are observed; stale setup stops later checks and audit
  failure reaches Make without performing installs or network operations.

  Validation: run focused criterion-marked cases and strict typecheck; review
  retained original covers markers, preparation obligations, and full CI.
