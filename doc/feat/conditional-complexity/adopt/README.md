# Adopt condition complexity guidance and checks

Deliver the [parent outcome](../README.md) after independent review of the
[investigation](../investigate/README.md). Start with a concrete compatible
candidate, threshold, supported settings, scope and bounded repair inventory;
unresolved gaps require maintainer steering before adoption.

Integrate guidance at
[engineering conventions](../../../engineering.md#code-style), reviewing the
surrounding composition/type-precision rules as a whole. Include a compact
seed-derived before/after example and clear distinctions between simple guards,
cohesive validation, function complexity and dense conditions. Cover `if`,
`elif` and `match` guards and prohibit relocating complexity or extracting
helpers merely to lower scores. Link to machine configuration rather than
duplicating settings inventories.

Add the reviewed complexipy development dependency and updated lockfile through
normal Make setup/locking. Reuse or minimally extend existing Make lint/CI
routes with focused path support and consistent file discovery. Apply
complementary Ruff settings only when supported by the reviewed evidence.
Findings above the adopted limit must fail with useful file/function/location
diagnostics and a repair direction; advisory output alone is insufficient.
Preserve agreed exact-threshold behavior. No snapshots or suppressions may
silently grandfather violations, and no broad exception may replace a bounded
repair.

Repair only violations necessary to enable prevention at the then-integrated
baseline. Preserve parent boundary/error behavior and existing types. Stop for a
reviewed split if policy/configuration/repairs exceed a short sitting. Permanent
tests exercise our integration and affected compatibility; upstream capability
probes belong to the investigation's historical evidence.

- **AC-1 TODO** Engineering guidance defines the condition-complexity ban,
  readable counterexamples and a seed-derived repair while accurately explaining
  tool limits, simple guards and cohesive extraction.

  Validation: independently review the affected engineering section and examples
  against the parent and investigation, including short-circuit type checks and
  dense match guards. Run documentation and acceptance checks.

- **AC-2 TODO** The locked reviewed complexipy candidate and any approved
  complementary Ruff configuration enforce agreed thresholds/scope through
  normal Make and required CI; focused paths and full discovery work
  consistently and the repository passes after bounded repairs.

  Validation: add criterion-marked integration regressions for our real Make
  routing/configuration using passing, exact-threshold and failing fixtures;
  assert statuses and useful diagnostics, focused scope and transient-directory
  exclusion. Run selected tests and lint through Make and inspect lock/setup/CI
  wiring. Full latest-head CI remains the ordinary merge gate.

- **AC-3 TODO** Necessary repairs preserve evaluation order, short-circuiting,
  exceptions and meaningful types, including all affected validator acceptance,
  rejection and extension compatibility.

  Validation: inspect affected call paths and run focused existing behavior/type
  checks through Make. Add criterion-marked regressions only for uncovered
  affected boundaries: missing/wrong-type/Boolean/negative identity, valid zero,
  lifecycle diagnostics, malformed persisted state and valid extensions. If no
  repairs are needed, independently review the inventory under this criterion.
