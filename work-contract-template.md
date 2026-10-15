# <Work name>

<!-- Replace the heading with the Work name and remove all instruction comments
before publishing. Keep only the relevant headings unless instruction comment says REQUIRED. -->

## Purpose

 <!-- Write one sentence stating why this change is needed. REQUIRED. -->

## Goals

<!-- List goals of this Work contract, each in one sentence. REQUIRED. -->

## Non-Goals

<!-- List non-goals of this Work contract, each in one sentence. REQUIRED. -->

## Mechanisms

<!-- List underlying mechanisms that will be used to solve this Work and describe their role in one sentence. Underlying mechanism can be 3rd party applications, CLI tools, or internal application packages, modules or data structures. Be specific when mechanism has many features, if e.g. designing sandboxes, list `codex sandbox` instead of only `codex`.

Example:

- `codex sandbox`: runs child commands with restricted filesystem access.
- `git worktree`: provide separate checkout directory to prevent concurrent edits issues.
-->

## Visuals

<!-- Mermaid graph or graphs as described in the guidance. -->

## Acceptance criteria

<!-- List of acceptance criteria. REQUIRED.

In the example, if a subheading of criterion would remain empty, then do not print it.

Example:

### **AC-1 TODO** Criterion name

Describe outcome of the criterion. List and describe created, removed and changed machinery. Focus on consumer facing outcomes from the perspective of a changed code or guidance. Include API with types if outcome is code.

Example:
Introduce `script/sandbox.py` module with a `create(path: Path)` API to be run via `make sandbox-create PATH=path`.

#### What exists

What exists right now and which requirements it already fulfills. Print it only if it helps explain that criterion.
-->

## Dependencies

<!-- List of links to other Works, including direct children, with one sentence description. Include guidaCan be empty if there are none, which means that is a leaf Work.

Example:

- TODO [Child Work name](child/README.md): Child purpose.
-->

## Links

<!-- List of other relevenant links, e.g. to previously closed Investigation or Evaluation Works with one sentence description of why are they relevant to this Work. -->

## Additional context

<!-- Prose that will be useful to include in this Work. Do not duplicate information from previous sections. Can remain empty if there are no such things. -->
