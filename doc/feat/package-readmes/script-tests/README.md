# Recent script test package documentation

## Purpose

Make script-test namespaces and their reusable support contracts discoverable.

## Goals

- Explain the direct contents and reusable APIs of `test/script` and its
  namespaces that contain owned code at delivery.
- Distinguish reusable helpers and fixtures from case-module behavior summaries.

## Acceptance criteria

### **AC-1 TODO** Complete script-test navigation and API ownership

Script-test readers can find every direct module and subpackage and understand
the active reusable helper and fixture contracts.

Reusable API descriptions agree with helpers, fixtures and their callers, with
fixtures described at their nearest owner. Existing case modules summarize the
behaviors they own separately from reusable API inventories, preserving the
distinction between unit and integration behavior where present.

Coverage follows current owned contents at delivery and does not require an
empty namespace README or new test cases.

### **AC-2 TODO** Accurate process and operational relationships

Script-test documentation explains canonical imports, actual process
boundaries and shared Make reuse while preserving existing operational notes.

Architecture and navigation follow the
[parent convention](../README.md#acceptance-criteria).

## Links

- [Package README coverage](../README.md): owns shared scope, convention,
  execution order and delivery conditions.

## Additional context

The proposed ordered leaves are overview, remaining helpers/fixtures, then
inventories of existing case namespaces, distinguishing unit and integration
cases where present. These remain planning slices, subject to the
[planning-before-package-edit gate](../README.md#additional-context).
Shared support README edits remain serial.
