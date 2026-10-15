# <Work name>

<!-- Replace the heading with the Work name and remove all instruction comments
before publishing. Keep only the relevant headings unless instruction comment says REQUIRED. Keep uniform vocabulary without mixing semantic meanings for a single word. Reuse the same word for the same meaning avoiding synonyms. -->

## Purpose

<!-- Write one sentence stating **why** this change is needed. REQUIRED. -->

## Goals

<!-- List goals of this Work contract, each in one sentence. This section is meant to summarize intended capabilities. REQUIRED. -->

## Glossary

<!-- Define terms whose meaning could be ambiguous in this Work. Reuse established repository meanings and link to shared definitions where useful. Omit this section when unnecessary.

Example:
- Model: a data structure whose constructor establishes its field and cross-field invariants.
-->

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

- Each criterion defines one observable outcome. Together, the criteria fulfill the Work’s purpose and goals.
- Name the outcome in the heading and state what becomes possible or changes when it is delivered.
- Include only the conditions, boundaries, and affected interfaces needed to determine completion.
- Split independently assessable outcomes into separate criteria.
- Describe the delivered result rather than listing implementation tasks or instructions to the executor.
- Leave implementation details owned by child Works in those contracts.

Omit empty criterion subheadings.
-->

<!-- AC code outcome example:

### **AC-1 TODO** Criterion name

`make sandbox-create PATH=path` creates a ready sandbox at an unused path. If the destination exists, it exits with status 2 without modifying it.

#### What exists

Describe existing behavior or machinery that helps explain this criterion, including what can be reused. Omit when unnecessary.
-->

<!-- AC guidance outcome example:

### **AC-2 TODO** Complete record validation

Engineering guidance requires constructors to validate every consumed field and cross-field invariant before returning a domain value. Rejection may stop at the first error; successful construction guarantees all invariants hold. A compact example shows valid construction and rejection of an invalid field combination.
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

<!-- Prose that will be useful to include in this Work. Do not duplicate information from previous headings. -->
