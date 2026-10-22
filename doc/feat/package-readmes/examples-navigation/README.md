# Examples and final package navigation

## Purpose

Complete example and test-root documentation and establish completeness across
the delivered package READMEs.

## Goals

- Explain the crossover strategy, its public interfaces and case module.
- Complete test-root namespace navigation and independently review overall
  coverage.

## Non-Goals

- Create empty README shells or an automated inventory framework.

## Inherited constraints

This Work inherits the parent's
[shared package README convention](../README.md#shared-package-readme-convention)
and
[scheduling and planning gate](../README.md#scheduling-and-planning-before-package-edit-gate).

- Independent review verifies the local example and test-root documentation.
- This Work owns final completeness review across the delivered packages.
- The parent owner uses that review to assess the combined result.

## Acceptance criteria

### **AC-1 TODO** Discoverable crossover strategy and interfaces

Readers can find the crossover strategy, its public interfaces and case module
and understand their responsibilities.

The example documentation explains the strategy and the responsibilities of
its interfaces and case module through descriptions that agree with the
implemented example.

### **AC-2 TODO** Independently reviewed final completeness

An independent final review establishes completeness across the delivered
documentation.

- The review finds no missing scoped package, direct content or API ownership.
- The review finds no broken operational or architecture link.

The review compares the delivered documentation with the full scoped
filesystem, exports and callers after preceding subtrees have delivered. Its
coverage includes architecture descriptions and preserved operational
navigation, so local subtree completeness alone does not establish this
criterion.

### **AC-3 TODO** Complete test-root navigation

Readers can navigate from the test root to every owned test namespace.

- Test-root navigation reaches the namespace READMEs.
- Data-only directories are described at their nearest owners under the
  inherited convention.

## Links

- [Package README coverage](../README.md): owns shared scope, convention,
  execution order and delivery conditions.

## Additional context

The proposed ordered leaves are example, test root, then final completeness
review. These remain planning slices, subject to the
[planning-before-package-edit gate](../README.md#scheduling-and-planning-before-package-edit-gate),
after the preceding subtrees.
