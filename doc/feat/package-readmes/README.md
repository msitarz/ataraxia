# Package README coverage

## Purpose

Make owned code and test namespaces discoverable through consistent READMEs
while preserving existing test operational notes.

## Goals

- Explain each scoped package's implemented purpose, architecture and direct
  contents.
- Describe reusable public APIs at their owners and provide reliable navigation.
- Establish lasting documentation guidance and same-change maintenance.

## Non-Goals

- Change runtime behavior or tooling policy.
- Add an inventory checker or generator.
- Create separate READMEs for data-only directories or empty README shells.

## Mechanisms

- Package READMEs explain owned namespaces and link readers to their contents
  and authoritative contracts.
- [Documentation ownership](../../README.md) is the lasting owner of the
  convention delivered by this Work.

### Shared package README convention

This parent owns the shared requirements for all children; the guidance child
establishes them at their lasting owner.

- Coverage includes `src/ataraxia` and compute, script, example and test
  namespace packages.
- Each README has a compact purpose and architecture explanation with Mermaid.
- Every direct owned module and subpackage has a link and one or two
  descriptive sentences.
- Subpackage detail belongs in its own README, while data and executable
  fixtures in data-only directories are described at the nearest owning README.
- Architecture descriptions agree with current code and authoritative contracts
  rather than presenting planned behavior as implemented.
- Each reusable public function, class, protocol, type alias and data structure
  has a one-sentence description, with classes' main operations described.
- API ownership reflects exports, callers and fixtures rather than imported
  third-party names or copied signatures.
- Reexports link to their owning module.
- Test case modules have summaries, while reusable helpers, fixtures and types
  have API descriptions.
- Existing commands and operational notes remain available.
- Documentation links to the authoritative contracts behind its descriptions.
- The lasting convention requires affected documentation to change alongside
  code.

Independent child review verifies this convention within each child's scope
against filesystem contents, exports, callers and fixtures. The parent owner
verifies the combined result using child review and the
[final completeness review](examples-navigation/README.md#ac-2-todo-independently-reviewed-final-completeness).
Review includes Mermaid rendering where available; unavailable rendering is an
explicit limitation and is not reported as observed rendering.

## Acceptance criteria

### **AC-1 TODO** Complete package navigation and architecture

Readers can navigate all scoped packages and understand their implemented
relationships across child boundaries.

Across the combined documentation, the
[shared convention](#shared-package-readme-convention) covers the scoped
filesystem without missing packages or direct owned contents. Purpose,
architecture and ownership descriptions agree at both ends of cross-package
links and distinguish current code from planned behavior.

### **AC-2 TODO** Discoverable reusable public APIs

Readers can follow each reusable public API to its owning module across the
combined documentation.

API coverage satisfies the
[shared convention](#shared-package-readme-convention), including reexports and
reusable test support. Descriptions identify ownership consistently across
packages.

### **AC-3 TODO** Preserved operational instructions

Readers retain operational guidance across the delivered packages.

Existing commands and operational notes remain reachable through the combined
navigation, and owner links lead to the authoritative contracts behind them.

### **AC-4 TODO** Discoverable lasting documentation upkeep

Contributors can find the convention that governs future package documentation
changes at its lasting owner.

The lasting guidance makes the same-change maintenance obligation discoverable
from the relevant engineering and testing guidance under the
[shared convention](#shared-package-readme-convention).

## Children

- **TODO** [Lasting package documentation guidance](guidance/README.md):
  Give the approved package README convention a lasting, discoverable owner.
- **TODO** [Recent script test package documentation](script-tests/README.md):
  Make script-test namespaces and their reusable support contracts discoverable.
- **TODO** [Make test package documentation](make-tests/README.md):
  Make Make-test interfaces, process boundaries and operational guidance
  discoverable.
- **TODO** [Product package documentation](product/README.md):
  Make product packages and their implemented public interfaces discoverable.
- **TODO** [Repository script documentation](scripts/README.md):
  Make repository scripts and their operational interfaces discoverable.
- **TODO** [Product test package documentation](product-tests/README.md):
  Make product-test coverage, reusable arrangements and checking routes
  discoverable.
- **TODO**
  [Examples and final package navigation](examples-navigation/README.md):
  Complete example and test-root documentation and establish completeness across
  the delivered package READMEs.

## Links

- [Documentation ownership](../../README.md): owns lasting documentation
  placement and maintenance rules.
- [Check and evidence policy](../../validation.md): owns check selection and the
  latest-head full CI merge gate.

## Additional context

### Scheduling and planning-before-package-edit gate

- Execute the children in listed order.
- Serialize edits to shared READMEs.
- Guidance is a leaf, while the other children require concrete, independently
  reviewed and merged leaf contracts before any package edits.
- Assess each complete delivery against the
  [review-effort boundary](../../workflow.md#scope-and-sizing) and split further
  when needed.

Final completeness review belongs to
[Examples and final package navigation](examples-navigation/README.md#ac-2-todo-independently-reviewed-final-completeness)
after preceding subtrees have delivered. Use the current documentation and
check owners above for Make-based formatting, link checks and delivery evidence.
