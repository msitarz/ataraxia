# Adopt condition complexity checks

## Purpose

Integrate the independently reviewed tool selection through normal Make/CI with
truthful limits and compatible bounded repairs.

## Goals

- Explain adopted tool coverage and its limits alongside existing policy.
- Enforce reviewed limits with locked dependencies and useful diagnostics.
- Enable enforcement through only necessary repairs.

## Non-Goals

- Redefine readable-condition or modeling policy.
- Resolve capability gaps by silently broadening exceptions or weakening limits.
- Extend repairs beyond violations needed at the then-integrated baseline.

## Mechanisms

- [Engineering conventions](../../../engineering.md) link tooling guidance to
  integrated validated-core policy.
- A locked reviewed complexipy candidate and evidence-supported complementary
  Ruff settings supply enforcement.
- Existing Make setup, locking, lint, and required CI own integration routes.
- Repository regressions cover configuration, routing, and affected
  compatibility.

## Acceptance criteria

### **AC-1 TODO** Truthful tool guidance

Engineering guidance explains adopted capabilities, limits, and remaining manual
review obligations, linking to
[integrated readable-condition policy](../../../engineering.md)
without duplicating it. The validated-core Work is a delivery dependency;
delivered guidance links to the lasting engineering owner rather than the
pending Work contract.

The explanation distinguishes function complexity from Boolean counting and
describes only coverage observed for the reviewed versions. Passing a metric
does not guarantee readability. Configuration is linked at its machine owner
rather than copied into a settings inventory; examples explain tool limitations
without requiring a historical sandbox repair.

### **AC-2 TODO** Blocking Make and CI enforcement

The locked reviewed candidate and any approved complementary settings enforce
agreed limits through normal Make and required CI.

- Setup and locking use existing Make machinery and include the updated
  lockfile.
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

### **AC-3 TODO** Compatible bounded repairs

The repository passes adopted enforcement after only necessary, independently
reviewable repairs at the then-integrated baseline, including when none are
needed.

Repairs preserve the
[parent supported-contract boundary](../README.md#shared-preservation-boundary),
meaningful types, and integrated validated-core guidance. Focused behavior and
type checks exercise actual affected supported contracts, with regressions only
for uncovered boundaries. Existing [testing guidance](../../../testing.md) owns
test placement: pure decisions use valid typed values, construction/ingress
tests exercise owned record invariants, and effects are covered at their adapter
or integration owner.

## Dependencies

- TODO [Capability and threshold investigation](../investigate/README.md)
  supplies the independently reviewed candidate, limits, scope, integration
  feasibility, and bounded repair inventory before adoption begins.
- TODO [Validated core guidance](../../validated-core/README.md) supplies
  integrated policy before adoption edits the shared engineering owner.

## Links

- [Parent contract](../README.md) owns tooling scope and preservation
  boundaries.

## Additional context

Unresolved capability gaps require steering before adoption. Integration or
repairs exceeding a short review sitting require a reviewed split under
[Work workflow](../../../workflow.md#scope-and-sizing).
