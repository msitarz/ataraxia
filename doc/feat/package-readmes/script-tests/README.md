# Recent script test package documentation

## Purpose

Make script-test namespaces and their reusable support contracts discoverable.

## Goals

- Explain the direct contents and reusable APIs of `test/script` and its
  namespaces that contain owned code at delivery.
- Distinguish reusable helpers and fixtures from case-module behavior summaries.

## Inherited constraints

This Work inherits the parent's
[shared package README convention](../README.md#shared-package-readme-convention)
and
[scheduling and planning gate](../README.md#scheduling-and-planning-before-package-edit-gate).
Independent review verifies the delivered script-test documentation against
these constraints; the parent verifies coverage across the combined result.

## Acceptance criteria

### **AC-1 TODO** Discoverable script-test contents and API owners

Script-test readers can find each owned module, namespace and reusable API from
the `test/script` documentation.

Navigation covers the direct contents of `test/script` and its namespaces that
contain owned code at delivery. Case-module summaries identify the behaviors
they own and distinguish unit and integration behavior where present. Reusable
API links lead to the helpers and fixtures that own those contracts.

Coverage follows current owned contents at delivery and does not require an
empty namespace README or new test cases.

### **AC-2 TODO** Accurate process and operational relationships

Readers can determine how script tests import support, cross process boundaries
and reuse Make support while retaining existing operational notes.

The documented imports are canonical, process descriptions match the processes
actually used by the tests, and Make relationships identify the shared support
they reuse.

### **AC-3 TODO** Understandable reusable support contracts

Readers can determine how to use the active reusable helpers and fixtures from
their API descriptions.

Descriptions agree with helper and fixture definitions and their callers.
Fixtures are described at their nearest owner, and reusable API descriptions
remain distinct from case-module behavior summaries.

## Links

- [Package README coverage](../README.md): owns shared scope, convention,
  execution order and delivery conditions.

## Additional context

The proposed ordered leaves are overview, remaining helpers/fixtures, then
inventories of existing case namespaces, distinguishing unit and integration
cases where present. These remain planning slices, subject to the
[planning-before-package-edit gate](../README.md#scheduling-and-planning-before-package-edit-gate).
Shared support README edits remain serial.
