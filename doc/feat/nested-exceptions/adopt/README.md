# Adopt nested exception guidance and prevention

Deliver the rule and behavior defined by the [parent contract](../README.md).
Depends on the independently reviewed
[Ruff investigation comparison](https://github.com/msitarz/ataraxia/blob/a0c90fe24cfa430a81b360fa10fd5aa13f8b2029/doc/feat/nested-exceptions/investigate/comparison.md).
That comparison found no precise supported Ruff mechanism. Adoption remains
blocked until the maintainer chooses to wait for a supported Ruff rule or
explicitly authorizes a narrowly scoped alternative, and the selected mechanism
and bounded repair inventory are concrete.

Integrate lasting guidance in
[engineering conventions](../../../engineering.md#code-style) alongside
composition and resource ownership. Explain forbidden lexical nesting, allowed
cleanup and separate scopes, cohesive helper extraction, and preserved exception
causes. Include a compact before/after example derived from the frozen seed with
the error and descriptor boundaries intact. Update surrounding prose as a whole;
do not create a second policy owner or a general decision journal.

Configure the supported Ruff mechanism in the existing configuration and reuse
blocking Make lint and CI checks. If the investigation proves Ruff insufficient,
use only the precise alternative explicitly authorized by the maintainer and
integrate it at the existing Make/CI boundary. Do not silently broaden nesting
limits, relax the guidance, add suppressions, or substitute advisory output for
failure. Diagnostics identify the offending file and location with a clear
repair direction. Include source, scripts and tests within existing lint scope.

Repair only violations necessary to adopt prevention at the then-integrated
baseline. PR #328 is independent; do not alter its branch or promise its seed
still needs repair. Preserve behavior through cohesive operations rather than
helper-per-line extraction. If the complete policy/configuration/repair diff
cannot fit a short review, pause the requested tree for a concrete bounded split
before implementation.

- **AC-1 TODO** Engineering conventions forbid the intended nested exception
  handlers with accurate allowed counterexamples and a seed-derived flattening
  example that preserves catching scopes, causes and descriptor ownership.

  Validation: independently review the whole affected code-style section and
  examples against the parent matrix and frozen source, including race-lost
  creation, validation/fsync failures and required cleanup. Run Make
  documentation and acceptance checks.

- **AC-2 TODO** The reviewed supported mechanism blocks every prohibited matrix
  arrangement and allows every permitted one through the repository's normal
  Make lint route and required CI checks, without unrelated blanket restrictions
  or exemptions. The repository passes the adopted lint after bounded repairs.

  Validation: add criterion-marked focused regressions for our configuration and
  command routing using representative prohibited and allowed fixtures; assert
  diagnostic location and nonzero/success statuses at the real Make boundary.
  Cover matrix distinctions without retesting upstream Ruff's algorithm. Run
  selected acceptance tests and normal lint through Make; independently inspect
  CI wiring. Full latest-head CI remains the ordinary merge gate.

- **AC-3 TODO** Any necessary code repairs preserve the original
  operation-specific catches, propagation/cause semantics and descriptor cleanup
  on success and failure, including ownership transfer of returned descriptors.

  Validation: review repaired call paths and run focused existing behavior tests
  through Make, adding criterion-marked regressions only for affected boundaries
  lacking coverage. Inject relevant operation failures to show `FileExistsError`
  is caught only for exclusive creation, validation/fsync errors propagate and
  descriptors close exactly once when owned locally. Test our refactoring
  behavior rather than OS locking itself. If no repairs are necessary, manually
  verify the inventory and record that evidence under this criterion.
