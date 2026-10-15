# Product test package documentation

## Purpose

Make product-test coverage, reusable arrangements and checking routes
discoverable.

## Goals

- Explain `test/ataraxia` and its unit, unit/compute, integration, acceptance
  and typecheck namespaces.
- Preserve test-type and command guidance while distinguishing runtime and type
  expectations.

## Acceptance criteria

### **AC-1 TODO** Complete product-test navigation and reusable API descriptions

Product-test readers can navigate every namespace and direct case module and
understand reusable arrangements and behavior coverage.

Reusable fixtures, helpers and types have API descriptions where present;
case modules have summaries rather than individual-test inventories.
Descriptions agree with filesystem contents and owned fixtures and types, and
case and source links follow the
[parent convention](../README.md#acceptance-criteria).

### **AC-2 TODO** Accurate checking routes and preserved operations

Readers can distinguish runtime tests from intentional-negative type
expectations and find their separate checking routes.

The documentation preserves existing test-type and command guidance, states
typecheck limits without claiming all legacy tests are strict, and links source
and testing owners without duplicating testing policy.

## Links

- [Package README coverage](../README.md): owns shared scope, convention,
  execution order and delivery conditions.

## Additional context

The proposed ordered leaves are overview, unit, unit/compute, integration,
acceptance, then typecheck. These remain planning slices, subject to the
[planning-before-package-edit gate](../README.md#additional-context).
