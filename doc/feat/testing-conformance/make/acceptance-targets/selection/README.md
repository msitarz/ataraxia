# Work and criterion selection

Migrate four Work/optional-criterion selection cases and two no-match cases.
Use a minimal typed disposable checkout/process helper copying the actual
Makefile, acceptance selector and required dependencies/configuration. Run real
nested pytest through real uv with explicit prepared offline environment and
timeouts. Put named pytest source fixtures under `test/make/fixtures` and copy
them into disposable `test/` and `example/` roots; do not generate source or
write fixtures into the checkout. Preserve selected/excluded witnesses and
real-tool markers; use precise exits and failure reasons, Given/When/Then, and
strict inclusion for new/cleaned modules, helpers and executable fixtures.
Support is narrowly reusable by declarations next; no generic fixture framework
or production changes. Leave declaration cases and their legacy support intact.

- **AC-1 TODO** Given marked cases in test and example roots, collect/test
  commands select all intended cases for a Work or only its requested criterion,
  exclude unrelated cases, and fail precisely when neither root has a match.

  Validation: run all six marked selection/no-match cases; independently review
  selected/excluded names, successful execution counts and exact no-match exits,
  disposable inputs and explicit environment, strict typecheck, and full CI.
