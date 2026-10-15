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

## Acceptance criteria

### **AC-1 TODO** Complete package navigation and architecture

Readers can navigate every scoped package and understand its implemented
relationships.

- Coverage includes `src/ataraxia` and compute, script, example and test
  namespace packages.
- Each README has a compact purpose and architecture explanation with Mermaid.
- Every direct owned module and subpackage has a link and one or two descriptive
  sentences.
- Subpackage detail belongs in its own README, while data and executable
  fixtures in data-only directories are described at the nearest owning README.
- Architecture descriptions agree with current code and authoritative contracts
  rather than presenting planned behavior as implemented.

### **AC-2 TODO** Discoverable reusable public APIs

Readers can find the reusable public API and its owning module without a
per-test-function inventory.

- Each reusable public function, class, protocol, type alias and data structure
  has a one-sentence description, with classes' main operations described.
- API ownership reflects exports, callers and fixtures rather than imported
  third-party names or copied signatures.
- Reexports link to their owning module.
- Test case modules have summaries, while reusable helpers, fixtures and types
  have API descriptions.

### **AC-3 TODO** Preserved operational instructions and upkeep

Readers retain existing commands and operational notes and can find the
authoritative contracts behind the documentation.

The lasting convention requires affected documentation to change alongside
code.

## Children

- **TODO** [Lasting package documentation guidance](guidance/README.md):
  establish the convention at its lasting owner.
- **TODO** [Recent script test packages](script-tests/README.md): document
  script-test namespaces and reusable support.
- **TODO** [Make test packages](make-tests/README.md): document Make-test
  boundaries, helpers and fixtures.
- **TODO** [Product packages](product/README.md): document product namespaces,
  APIs and implemented relationships.
- **TODO** [Repository scripts](scripts/README.md): document script entry points
  and operational interfaces.
- **TODO** [Product test packages](product-tests/README.md): document
  product-test namespaces and checking routes.
- **TODO** [Examples and final navigation](examples-navigation/README.md):
  document examples and test-root navigation and review final completeness.

## Links

- [Documentation ownership](../../README.md): owns lasting documentation
  placement and maintenance rules.
- [Check and evidence policy](../../validation.md): owns check selection and the
  latest-head full CI merge gate.

## Additional context

- Execute the children in listed order.
- Serialize edits to shared READMEs.
- Guidance is a leaf, while the other children require concrete, independently
  reviewed and merged leaf contracts before any package edits.
- Assess each complete delivery against the
  [review-effort boundary](../../workflow.md#scope-and-sizing) and split further
  when needed.

Independent delivery review compares architecture, module, API and navigation
descriptions with current filesystem contents, exports, callers and fixtures
and can reuse child review. Final completeness review belongs to
[Examples and final navigation](examples-navigation/README.md#ac-2-todo-independently-reviewed-final-completeness).

Delivery review includes Mermaid rendering where available; unavailable
rendering remains an explicit limitation and is not reported as observed
rendering. Use the current documentation and check owners above for Make-based
formatting, link checks and delivery evidence rather than duplicating their
policies here.
