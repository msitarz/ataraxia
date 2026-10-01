# Coverage checker

Add a bounded checker for one active Work contract at a time. It reports
declared coverage only; it does not run tests, query CI, or decide whether the
criterion's behavior is adequately verified. Read the shared
[acceptance-tracing owner](../../../../../../acceptance-tracing.md) before
implementation.

## Acceptance

- Expose `make ac-check WORK=path/to/README.md` for one existing, repository-
  relative Work `README.md` or `spec.md`, matching the path validation used by
  `ac-collect` and `ac-test`. Check the full contract; no `AC` selector or
  repository-wide Work discovery is needed.
- Extend the acceptance-tracing owner with one parseable criterion form, one
  criterion per Markdown list item: `- **AC-1 TODO** ...` or
  `- **AC-1 DONE** ...`. Keep the existing ID scope and TODO/DONE meanings.
  For declared non-test coverage, require a non-empty `Verification: ...`
  annotation on that item. For a removed temporary probe with an active AC,
  retain its one-time method and delivery PR link beside the criterion as
  test ownership requires. Keep the documented literal pytest marker syntax
  unchanged.
- Parse declarations from the selected Work and marker decorators from
  `test/**/*.py`. Initially support the documented
  `@pytest.mark.covers(work="...", ac="AC-1")` form with literal arguments
  (including repeated decorators for multiple criteria); report unsupported
  dynamic `covers` arguments clearly instead of executing Python tests.
- Fail with the Work path and criterion ID for duplicate or malformed
  declarations, a marker for the selected Work that names no declared AC, or a
  `DONE` AC with neither a matching test marker nor an explicit verification
  annotation. A `TODO` without coverage remains valid; never rewrite statuses.
- Ignore markers for other Work paths, including removed historical Works.
  Require the selected `WORK` file to exist; do not scan Git history, delete
  retained historical markers, or add an active-Work registry. During Work
  removal, compare its criteria with retained tests and non-test methods in the
  delivery PR. Keep markers and docstrings on retained tests as historical
  behavior records; the checker must ignore their missing Work paths. Delivery
  cleanup follows the existing
  [Work lifecycle](../../../../../../workflow.md) and
  [test ownership](../../../../../../test-ownership.md).
- Add focused checker tests for valid `TODO`/`DONE` cases, missing/unknown
  references, duplicate IDs, explicit non-test coverage, unsupported marker
  expressions, and an unrelated or historical marker. Keep Markdown formatting
  and link validation with rumdl; do not implement a second Markdown checker.

## Implementation plan

Add a focused Python checker under `script/` and route it through
`make ac-check`. Reuse the current Make `WORK` path contract, the declared
marker form, and the coverage meanings in the permanent owner. Keep the check
read-only and limited to the selected Work plus marker declarations in test
sources. No plugin, status snapshots, CI evidence, or test execution is part of
the checker.
