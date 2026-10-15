# Repository script documentation

## Purpose

Make repository scripts and their operational interfaces discoverable.

## Goals

- Explain direct scripts, implemented command entry points and reusable
  functions and types.
- Connect script responsibilities to Make and authoritative workflow contracts.

## Acceptance criteria

### **AC-1 TODO** Complete script navigation and interface descriptions

Script readers can locate every direct script and understand its implemented
entry-point and reusable interfaces.

Python descriptions agree with exports and callers. Shell interfaces describe
actual arguments, environment and effects as used by invocation sites without
copying implementation or inventing APIs.

### **AC-2 TODO** Preserved operational contracts and commands

Readers can understand shell responsibilities and script relationships to Make
and owning workflow contracts while retaining existing commands and operational
constraints.

Module summaries, API descriptions and owner links follow the
[parent convention](../README.md#acceptance-criteria).

## Links

- [Package README coverage](../README.md): owns shared scope, convention,
  execution order and delivery conditions.

## Additional context

The proposed ordered leaves are Python scripts, then shell scripts. These
remain planning slices, subject to the
[planning-before-package-edit gate](../README.md#additional-context).
