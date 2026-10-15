# Adopt condition complexity guidance and checks

## Purpose

Deliver readable-condition guidance and blocking checks through the normal
Make/CI boundary using the independently reviewed investigation outcome.

## Goals

- Integrate lasting guidance that explains readable conditions and truthful tool
  limits.
- Enforce the reviewed thresholds and scope with a locked dependency and useful
  diagnostics.
- Enable enforcement through bounded repairs that preserve affected behavior.

## Non-Goals

- Resolve investigation capability gaps by silently broadening exceptions or
  weakening thresholds.
- Extend repairs beyond violations necessary for enforcement at the
  then-integrated baseline.

## Mechanisms

- [Engineering conventions](../../../engineering.md#code-style) own the adopted
  guidance alongside composition and type-precision rules.
- A locked complexipy development dependency and evidence-supported
  complementary Ruff settings provide automatic checks.
- Existing Make setup, locking, lint, and required CI routes provide dependency
  management and enforcement.
- Repository integration regressions cover configuration, routing, and affected
  compatibility rather than upstream scoring algorithms.

## Acceptance criteria

### **AC-1 TODO** Readable condition guidance

Engineering guidance defines the
[parent condition-complexity boundary](../README.md#shared-guidance-boundary)
with readable counterexamples and a compact seed-derived before/after repair.

- The guidance integrates with the surrounding composition and type-precision
  rules and links to integrated validated boundary rules instead of duplicating
  them.
- Examples distinguish simple guards, complete consumed-record validation, typed
  pure decisions, function complexity, and dense conditions, including type
  prerequisites and dense `match` guards.
- The explanation accurately describes the reviewed tool limits, remaining
  manual review obligations, and cohesive extraction.
- Machine configuration is linked rather than copied into a settings inventory.

### **AC-2 TODO** Blocking Make and CI enforcement

The locked reviewed candidate and any approved complementary Ruff settings
enforce the agreed limits through normal Make and required CI.

- Dependency setup and locking use the existing Make machinery and include the
  updated lockfile.
- Focused paths and full discovery apply the agreed scope consistently,
  excluding transient directories.
- Findings above the adopted limit fail with useful file, function, and location
  diagnostics and a repair direction, while exact-threshold behavior matches the
  reviewed recommendation.
- Passing, exact-threshold, and failing cases through the real Make route
  demonstrate statuses, diagnostics, focused scope, and transient-directory
  exclusion.
- Retained integration regressions exercise repository routing and configuration
  under [test ownership](../../../test-ownership.md).
- Snapshots, suppressions, or broad exceptions do not silently grandfather
  violations or replace bounded repairs.

### **AC-3 TODO** Compatible bounded repairs

The repository passes the adopted enforcement after only necessary repairs at
the then-integrated baseline.

- Repairs preserve the
  [parent preservation boundary](../README.md#shared-preservation-boundary),
  existing meaningful types, and integrated validated boundary guidance.
- The repair inventory is independently reviewable even if no repairs are
  needed.
- Focused existing behavior and type checks cover affected call paths and the
  parent seed boundaries, including valid zero, with regressions added only for
  uncovered affected boundaries.
- Pure-rule tests use valid typed values.
- Constructor and boundary tests cover whole consumed records and cross-field
  failures.
- Effects remain covered at their owning adapter or integration boundary under
  existing [testing guidance](../../../testing.md).

## Dependencies

- TODO [Capability and threshold investigation](../investigate/README.md)
  supplies the independently reviewed compatible candidate, threshold, supported
  settings, scope, and bounded repair inventory required before adoption begins.
- TODO [Validated core guidance](../../validated-core/README.md) supplies
  integrated boundary rules before this Work edits the shared engineering owner.

## Links

- [Parent contract](../README.md) owns shared scope, guidance, preservation
  boundaries, and the frozen seed.

## Additional context

Unresolved capability gaps require maintainer steering before adoption.
Policy, configuration, or repairs that exceed a short review sitting require a
reviewed split under the [Work workflow](../../../workflow.md#scope-and-sizing).
