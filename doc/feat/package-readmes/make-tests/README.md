# Make test package documentation

## Purpose

Make Make-test interfaces, process boundaries and operational guidance
discoverable.

## Goals

- Explain `test/make` and its integration namespace, including reusable helpers
  and fixtures.
- Preserve real-tool selection commands and prepared-environment notes.

## Acceptance criteria

### **AC-1 TODO** Complete Make-test navigation and interface descriptions

Make-test readers can navigate every direct owned module and subpackage and
distinguish reusable sandbox, recorder and worktree interfaces from
case-module contracts.

Helper and recorder descriptions agree with real callers, fixture
responsibilities are described at their nearest owner, and executable fixtures
remain discoverable.

### **AC-2 TODO** Accurate tool boundaries and preserved operations

Readers can understand real Make, Git and tool boundaries and process isolation
while retaining `real_tool` selection commands and prepared-environment notes.

Architecture and navigation include accurate script-owner links and follow the
[parent convention](../README.md#acceptance-criteria).

## Links

- [Package README coverage](../README.md): owns shared scope, convention,
  execution order and delivery conditions.

## Additional context

The proposed ordered leaves are overview, sandbox/recorder, worktree helpers,
then integration and executable fixtures. These
remain planning slices, subject to the
[planning-before-package-edit gate](../README.md#additional-context).
