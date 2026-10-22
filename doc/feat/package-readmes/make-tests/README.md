# Make test package documentation

## Purpose

Make Make-test interfaces, process boundaries and operational guidance
discoverable.

## Goals

- Explain `test/make` and its integration namespace, including reusable helpers
  and fixtures.
- Preserve real-tool selection commands and prepared-environment notes.

## Inherited constraints

This Work inherits the parent's
[shared package README convention](../README.md#shared-package-readme-convention)
and
[scheduling and planning gate](../README.md#scheduling-and-planning-before-package-edit-gate).
Independent review verifies the delivered Make-test documentation against these
constraints; the parent verifies coverage across the combined result.

## Acceptance criteria

### **AC-1 TODO** Discoverable Make-test contents and interfaces

Make-test readers can locate the owned contents of `test/make` and its
integration namespace and find their documented interfaces.

Navigation reaches every direct owned module and subpackage, including
executable fixtures. Summaries distinguish case-module contracts from reusable
sandbox, recorder and worktree interfaces.

### **AC-2 TODO** Accurate tool boundaries and preserved operations

Readers can understand real Make, Git and tool boundaries and process isolation
while retaining `real_tool` selection commands and prepared-environment notes.

Architecture descriptions identify the actual process boundaries, and links
lead to the scripts that own the described operations.

### **AC-3 TODO** Understandable reusable helpers and fixtures

Readers can determine the responsibilities and use of Make-test helpers,
recorders and fixtures from their owning documentation.

Helper and recorder API descriptions agree with real callers. Fixture
responsibilities are described at their nearest owner, including the role of
executable fixtures.

## Links

- [Package README coverage](../README.md): owns shared scope, convention,
  execution order and delivery conditions.

## Additional context

The proposed ordered leaves are overview, sandbox/recorder, worktree helpers,
then integration and executable fixtures. These
remain planning slices, subject to the
[planning-before-package-edit gate](../README.md#scheduling-and-planning-before-package-edit-gate).
