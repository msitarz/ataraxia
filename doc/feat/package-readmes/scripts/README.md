# Repository script documentation

## Purpose

Make repository scripts and their operational interfaces discoverable.

## Goals

- Explain direct scripts, implemented command entry points and reusable
  functions and types.
- Connect script responsibilities to Make and authoritative workflow contracts.

## Inherited constraints

This Work inherits the parent's
[shared package README convention](../README.md#shared-package-readme-convention)
and
[scheduling and planning gate](../README.md#scheduling-and-planning-before-package-edit-gate).

- Independent review verifies the delivered script documentation against these
  constraints.
- The parent verifies coverage across the combined result.

## Acceptance criteria

### **AC-1 TODO** Discoverable scripts and interfaces

Readers can locate every direct repository script and find its implemented
command entry points and reusable functions and types.

Each script summary identifies its responsibility and leads to its interface
description.

### **AC-2 TODO** Preserved operational contracts and commands

Readers can understand shell responsibilities and script relationships to Make
and owning workflow contracts.

- Existing commands remain available.
- Existing operational constraints remain available.
- Links connect the scripts to the Make invocations and workflow contracts that
  own those operational requirements.

### **AC-3 TODO** Accurate Python and shell interface descriptions

Readers can determine how repository scripts are used from descriptions of
their implemented interfaces.

- Python API descriptions agree with exports and callers.
- Shell interface descriptions state actual arguments, environment and effects
  as used by invocation sites.
- Shell interface descriptions do not copy implementation.
- Shell interface descriptions do not invent APIs.

## Links

- [Package README coverage](../README.md): owns shared scope, convention,
  execution order and delivery conditions.

## Additional context

The proposed ordered leaves are Python scripts, then shell scripts. These
remain planning slices, subject to the
[planning-before-package-edit gate](../README.md#scheduling-and-planning-before-package-edit-gate).
