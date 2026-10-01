# Acceptance tool scope

Make acceptance declaration checking, collection, and execution support Work
tests consistently under both `test/` and `example/`.

The [coverage checker](../../../../../script/acceptance_coverage.py) scans only
`test/`. The [test selector](../../../../../script/acceptance_tests.py) relies
on pytest's default `test/` discovery. Example tests run separately in CI, so a
valid Work marker there is invisible to both acceptance paths.

Extend the acceptance tools and their
[documentation](../../../../acceptance-tracing.md) coherently. Keep the normal
test suite and separate example CI targets at their existing scope; reuse a
shared definition for acceptance test roots where practical.

## Acceptance

- **AC-1 TODO** Given one marked test under `test/` and one under `example/`
  for the same Work, `ac-check` reports both declarations and `ac-collect`
  selects both tests, excluding other Works.
- **AC-2 TODO** `ac-test` executes both selected tests; selecting one criterion
  excludes the other, and selecting an absent criterion fails rather than
  reporting success.
- **AC-3 TODO** Default full tests and the dedicated example target retain their
  previous scopes, while documentation describes the shared acceptance scope
  and existing limits of static marker inspection.

Verify through the public Make targets with temporary Work contracts and tests.
Retain concrete regression coverage for selection and declaration behavior.
