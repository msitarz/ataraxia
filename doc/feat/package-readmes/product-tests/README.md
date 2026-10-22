# Product test package documentation

## Purpose

Make product-test coverage, reusable arrangements and checking routes
discoverable.

## Goals

- Explain `test/ataraxia` and its unit, unit/compute, integration, acceptance
  and typecheck namespaces.
- Preserve test-type and command guidance while distinguishing runtime and type
  expectations.

## Inherited constraints

This Work inherits the parent's
[shared package README convention](../README.md#shared-package-readme-convention)
and
[scheduling and planning gate](../README.md#scheduling-and-planning-before-package-edit-gate).

- Independent review verifies the delivered product-test documentation against
  these constraints.
- The parent verifies coverage across the combined result.

## Acceptance criteria

### **AC-1 TODO** Discoverable product-test contents and API owners

Readers can navigate `test/ataraxia` and its unit, unit/compute, integration,
acceptance and typecheck namespaces and find their reusable APIs.

- Navigation reaches every namespace and direct case module in that scope.
- Case-module summaries identify behavior coverage.
- Case and source links reach their corresponding owners.

### **AC-2 TODO** Accurate checking routes and preserved operations

Readers can distinguish runtime tests from intentional-negative type
expectations and find their separate checking routes.

- The documentation preserves existing test-type and command guidance.
- The documentation states typecheck limits without claiming all legacy tests
  are strict.
- The documentation links to source and testing owners.
- The documentation does not duplicate testing policy.

### **AC-3 TODO** Understandable reusable test arrangements

Readers can determine the responsibilities and use of reusable product-test
fixtures, helpers and types where present.

- Their API descriptions agree with filesystem contents and the owned fixtures
  and types.
- Reusable arrangements remain distinct from case-module summaries and
  individual-test inventories.

## Links

- [Package README coverage](../README.md): owns shared scope, convention,
  execution order and delivery conditions.

## Additional context

The proposed ordered leaves are overview, unit, unit/compute, integration,
acceptance, then typecheck. These remain planning slices, subject to the
[planning-before-package-edit gate](../README.md#scheduling-and-planning-before-package-edit-gate).
