# Test layout

Separate product tests from repository script and Make target tests while
preserving behavior and existing lint policy. Keep filenames and test-type
classifications. Example tests remain under `example/`; Ruff configurations
and test-quality cleanup are deferred.

## Acceptance criteria

- **AC-1 DONE** Tests, registry fixtures, and helpers are grouped by the
  component whose contract they assert under `test/ataraxia`, `test/script`,
  and `test/make`, with one authoritative registry fixture implementation.

  Validation: Independently review the move mapping and fixture reuse against
  the approved ownership split.
- **AC-2 DONE** All existing tests and parametrized cases remain discoverable
  and runnable; type contracts and routing checks use the relocated paths.

  Validation: Compare pre/post collection after normalizing moved path prefixes;
  run each ownership suite independently, full `make test`, and
  `make typecheck-expectations`.
- **AC-3 DONE** Current guidance and navigation resolve to the new layout,
  without new lint policy or unrelated test changes.

  Validation: Review the diff
  and current path references; run `make lint-check`, `make format-check`, and
  `make doc-check`. Preserve historical records.
