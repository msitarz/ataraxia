# <Work name>

<!-- Replace the heading with the Work name and remove all instruction comments
before publishing. Keep only the relevant headings unless instruction comment says REQUIRED. -->

## Purpose

 <!-- Write one sentence stating **why** this change is needed. REQUIRED. -->

## Goals

<!-- List goals of this Work contract, each in one sentence. This section is meant to summarize intended capabilities. REQUIRED. -->

## Non-Goals

<!-- List non-goals of this Work contract, each in one sentence. -->

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

Acceptance criteria define completion of this Work, which must cover Goals. A single acceptance criterion might cover multiple goals. Multiple acceptance criteria might cover a single goal.

In the example, if a subheading of criterion would remain empty, then do not print it the heading as well.

Example:

### **AC-1 TODO** Criterion name

Describe outcome of the criterion. List and describe created, removed and changed machinery in accordance to the purpose of this Work and criterion. Do not describe internal machinery that might be covered by children Works. Keep the Focus on consumer facing outcomes from the perspective of a changed code or guidance. Include consumer interface with types if the outcome is code.

Example:
Introduce `make sandbox-create PATH=path` creates a ready sandbox at an unused path. If the destination exists, it exits with status 2 without modifying it.

#### What exists

What machinery exists right now but should be modified or expanded. Print it only if it helps explain that criterion.
-->

## Dependencies

<!-- List of links to other Works, their purpose and prerequisite explanation. Do **NOT** include direct children.

Example:

- TODO [Dependency Work name](link/to/work/README.md): Dependency purpose from its Work contract.
    It provides API or mechanism that this Work consumes.
-->

## Children

<!-- List of links to direct children Works, with one sentence description.

Example:

- TODO [Child Work name](child/README.md): Child purpose.
-->

## Links

<!-- List of other relevant links, e.g. to previously closed Investigation or Evaluation Works with one sentence description of why are they relevant to this Work. -->

## Additional context

<!-- Prose that will be useful to include in this Work. Do not duplicate information from previous sections. Can remain empty if there are no such things. -->
