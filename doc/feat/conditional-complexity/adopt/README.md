# Adopt condition complexity checks

## Purpose

Integrate the independently reviewed complexipy release through normal Make/CI
with truthful limits and compatible bounded repairs.

## Goals

- Explain adopted tool coverage and its limits alongside existing policy.
- Enforce reviewed limits with locked dependencies and useful diagnostics.
- Enable enforcement through only necessary repairs.

## Non-Goals

- Redefine readable-condition or modeling policy.
- Resolve capability gaps by silently broadening exceptions or weakening limits.
- Extend repairs beyond violations needed at the then-integrated baseline.

## Mechanisms

- Engineering conventions own adopted tool guidance alongside readable-condition
  policy.
- The locked reviewed complexipy release and evidence-supported complementary
  Ruff settings supply enforcement.
- Existing Make setup, locking, lint, and required CI own integration routes.
- Repository regressions cover configuration, routing, and affected
  compatibility.

## Acceptance criteria

### **AC-1 DONE** Truthful tool guidance

Engineering guidance explains adopted capabilities, limits, and remaining manual
review obligations, linking to
[integrated readable-condition policy](../../../engineering.md)
without duplicating it. Engineering guidance is the lasting policy owner.

The explanation distinguishes function complexity from Boolean counting and
describes only coverage observed for the reviewed versions. Passing a metric
does not guarantee readability. Configuration is linked at its machine owner
rather than copied into a settings inventory; examples explain tool limitations
without requiring a historical sandbox repair.

### **AC-2 DONE** Blocking Make and CI enforcement

The locked reviewed release and any approved complementary settings enforce
agreed limits through normal Make and required CI.

- Setup and locking use existing Make machinery and include the updated
  lockfile.
- The `pyproject.toml` dev dependency is
  `complexipy>=<latest assessed version>`; `uv.lock` records the exact resolved
  release whose behavior supports adoption evidence.
- Focused paths and full discovery apply reviewed scope consistently, excluding
  transient directories.
- Above-limit findings fail with useful file, function, and location diagnostics
  and a repair direction; exact-threshold behavior matches the recommendation.
- Passing, exact-threshold, and failing cases through the real Make route
  demonstrate statuses, diagnostics, focused scope, and transient exclusion.
- Retained integration regressions cover repository configuration and routing
  under [test ownership](../../../test-ownership.md).
- Snapshots, suppressions, or broad exceptions do not silently grandfather
  violations or replace bounded repairs.

One-time real-route results are recorded in
[AC-2 observations](observations.md).

### **AC-3 DONE** Compatible bounded repairs

The repository passes adopted enforcement after only necessary, independently
reviewable repairs at the then-integrated baseline, including when none are
needed.

Repairs preserve the
[parent supported-contract boundary](../README.md#shared-preservation-boundary),
meaningful types, and integrated engineering guidance. Focused behavior and
type checks exercise actual affected supported contracts, with regressions only
for uncovered boundaries. Existing [testing guidance](../../../testing.md) owns
test placement: pure decisions use valid typed values, construction/ingress
tests exercise owned record invariants, and effects are covered at their adapter
or integration owner.

## Dependencies

- DONE
  [Reviewed Complexipy 8.0.1 investigation](https://github.com/msitarz/ataraxia/blob/2416d974065d9086f8123baeae76a3c95057598d/doc/feat/conditional-complexity/investigate/findings.md)
  supplies the release, inclusive 15 limit, Ruff PLR0916/max-five complement,
  scope, integration feasibility, and bounded repair inventory.
- DONE [Integrated engineering guidance](../../../engineering.md) supplies
  policy consumed by adoption.

## Links

- [Parent contract](../README.md) owns tooling scope and preservation
  boundaries.

## Additional context

- Use `complexipy>=8.0.1` in the dev dependency group and lock the assessed
  release; enforce inclusive 15 with Ruff PLR0916 at its default maximum of
  five.
- Reuse path-only `ARGS` with default `.`, one Ruff call per lint route, native
  Complexipy, SARIF line locations, and matching `build`/`dist` exclusions;
  score functions without enabling module-level script bodies.
- Bound repairs to `read_calls`, `check_work`, and `check_root_owner`, with
  tests for returned records, caller-visible errors, diagnostics, and ownership
  safety.
- Keep manual review for uncovered Boolean forms including `match` guards;
  the release source resolves current documentation's scoring discrepancies,
  while runtime behavior outside macOS remains unobserved.

Unresolved capability gaps require steering before adoption. Integration or
repairs exceeding a short review sitting require a reviewed split under
[Work workflow](../../../workflow.md#scope-and-sizing).
