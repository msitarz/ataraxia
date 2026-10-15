# Product package documentation

## Purpose

Make product packages and their implemented public interfaces discoverable.

## Goals

- Explain every direct owned module and subpackage of `src/ataraxia` and
  compute.
- Relate reusable public APIs to their owners and current architecture.

## Acceptance criteria

### **AC-1 TODO** Complete product navigation and API ownership

Product READMEs expose every direct owned module and subpackage and reusable
public API, including exports, reexport owners and classes' main operations.

Descriptions agree with exports and callers and follow the
[parent convention](../README.md#acceptance-criteria).

### **AC-2 TODO** Accurate implemented product relationships

Readers can relate graphs, runners, providers, features and entry points to
current architecture and ADRs through accurate descriptions and authoritative
links.

The READMEs do not restate those contracts or present planned deployment as
implemented behavior.

## Links

- [Package README coverage](../README.md): owns shared scope, convention,
  execution order and delivery conditions.

## Additional context

The proposed ordered leaves are compute, root overview, bar/broker/errors,
provider/source/feature, then backtest/CLI/util. These remain planning slices,
subject to the
[planning-before-package-edit gate](../README.md#additional-context).
Root API and navigation edits follow compute and remain serial.
