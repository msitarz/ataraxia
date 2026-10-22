# Product package documentation

## Purpose

Make product packages and their implemented public interfaces discoverable.

## Goals

- Explain every direct owned module and subpackage of `src/ataraxia` and
  compute.
- Relate reusable public APIs to their owners and current architecture.

## Inherited constraints

This Work inherits the parent's
[shared package README convention](../README.md#shared-package-readme-convention)
and
[scheduling and planning gate](../README.md#scheduling-and-planning-before-package-edit-gate).

- Independent review verifies the delivered product documentation against these
  constraints.
- The parent verifies coverage across the combined result.

## Acceptance criteria

### **AC-1 TODO** Discoverable product contents and API owners

Readers can locate every direct owned module, subpackage and reusable public
API through the `src/ataraxia` and compute READMEs.

Navigation identifies API owners from exports and callers, including the owning
module behind each reexport.

### **AC-2 TODO** Accurate implemented product relationships

Readers can relate graphs, runners, providers, features and entry points to
current architecture and ADRs through accurate descriptions and authoritative
links.

- The READMEs do not restate those contracts.
- The READMEs do not present planned deployment as implemented behavior.

### **AC-3 TODO** Understandable product API responsibilities

Readers can determine the responsibilities of reusable public interfaces and
classes' main operations from their owning documentation.

API descriptions agree with exports and callers in `src/ataraxia` and compute,
so following a navigation link reaches an explanation of the implemented
interface.

## Links

- [Package README coverage](../README.md): owns shared scope, convention,
  execution order and delivery conditions.

## Additional context

The proposed ordered leaves are compute, root overview, bar/broker/errors,
provider/source/feature, then backtest/CLI/util. These remain planning slices,
subject to the
[planning-before-package-edit gate](../README.md#scheduling-and-planning-before-package-edit-gate).
Root API and navigation edits follow compute and remain serial.
