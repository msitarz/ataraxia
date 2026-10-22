# Lasting package documentation guidance

## Purpose

Give the approved package README convention a lasting, discoverable owner.

## Goals

- Establish the convention and same-change maintenance obligation at
  documentation ownership.
- Make the convention discoverable from engineering and testing guidance without
  duplicating their rules.

## Non-Goals

- Change package READMEs or tooling.
- Add package inventories to this guidance revision.

## Mechanisms

- [Documentation ownership](../../../README.md) holds the lasting package README
  convention, with links from engineering and testing guidance.

## Inherited constraints

This Work inherits the parent's
[shared package README convention](../README.md#shared-package-readme-convention)
and
[scheduling and planning gate](../README.md#scheduling-and-planning-before-package-edit-gate).

- Independent review verifies the guidance against those constraints.
- Package coverage remains subject to the parent's combined review.

## Acceptance criteria

### **AC-1 TODO** Coherent and discoverable package guidance

Readers can find the package README convention at documentation ownership from
the relevant engineering and testing guidance.

- The lasting owner states the inherited convention.
- Adjacent guidance links there as needed.
- The owning and adjacent guidance retains existing documentation ownership,
  navigation and operational requirements.
- The owning and adjacent guidance contains no contradictory architecture, API
  or test rules.
- The owning and adjacent guidance contains no duplicated architecture, API or
  test rules.
- Representative product and test examples demonstrate the same convention.

### **AC-2 TODO** Discoverable same-change maintenance obligation

Contributors can determine when a code change requires a documentation update
from the lasting guidance.

Documentation ownership states the inherited same-change maintenance obligation
alongside the package convention, so contributors do not need this Work
contract to find that obligation.

## Links

- [Package README coverage](../README.md): owns shared scope, convention,
  execution order and delivery conditions.
