# <Work name>

<!-- Replace the heading with the Work name and remove all instruction comments
before publishing. Keep only the relevant headings unless instruction comment says REQUIRED. Use each term consistently; avoid synonyms for the same concept. Use relative Markdown links. -->

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

<!-- Use an unordered list with one sentence per mechanism, naming the tool, package, module, or data structure central to the solution and explaining its role. Be specific—for example, `codex sandbox` rather than `codex`. Put acceptance requirements in the relevant AC. Keep necessary shared contracts in clearly named subsections, using single-sentence bullets for parallel rules.

Example:

- `codex sandbox`: runs child commands with restricted filesystem access.
- `git worktree`: provide separate checkout directory to prevent concurrent edits issues.
-->

## Visuals

<!-- For meaningful architecture, module relationships, interactions, or lifecycle changes, show proportionate before/after visuals using a suitable GitHub-supported Mermaid type. Tiny changes may use clear before/after prose.

Inspect current source or contracts and identify the verified before revision. Distinguish proposed additions, changes, and removals; label historical or illustrative designs, and correct the proposal when verified implementation differs. Show only affected context.

Check diagram accuracy against source and contracts. Use real Mermaid fences so `make doc-check` validates rendering syntax; passing rendering does not establish acceptance or GitHub/browser parity.
-->

## Acceptance criteria

<!-- List of acceptance criteria. REQUIRED.

- Each criterion defines one observable outcome. Together, the criteria fulfill the Work’s purpose and goals.
- Name the outcome in the heading and start each criterion with a short sentence stating what becomes possible or changes when it is delivered.
- Use short prose for connected explanations and unordered, single-sentence bullets for parallel conditions, guarantees, or refusal cases.
- Include preconditions, expected results, relevant failure/preservation boundaries, and affected interfaces with useful signatures and types needed to determine completion. Describe inputs, outputs, behavior, and compatibility changes where relevant.
- State measurement thresholds and the conditions needed to interpret them in the outcome when they define success.
- Split independently assessable outcomes into separate criteria.
- Describe the delivered result rather than listing implementation tasks or instructions to the executor.
- Keep each requirement at one owner and link to it elsewhere; leave implementation details owned by child Works in those contracts.

Omit empty criterion subheadings.
-->

<!-- AC code outcome example:

### **AC-1 TODO** Create a sandbox at an unused path

`make sandbox-create PATH=path` creates a ready sandbox at an unused path. If the destination exists, it exits with status 2 without modifying it.

#### What exists

Describe existing behavior or machinery that helps explain this criterion, including what can be reused. Omit when unnecessary.
-->

<!-- AC guidance outcome example:

### **AC-2 TODO** Complete record validation

Engineering guidance requires constructors to validate every consumed field and cross-field invariant before returning a domain value. Rejection may stop at the first error; successful construction guarantees all invariants hold. A compact example shows valid construction and rejection of an invalid field combination.
-->

## Dependencies

<!-- List of prerequisite Works, their purpose, and prerequisite explanation. Do **NOT** include direct children. Use `STATUS [Work title](path/to/README.md): purpose.` Ordinary guidance links have no Work status. Keep purpose text aligned with the linked Work. See [Work lifecycle](workflow.md#lifecycle) for status and closure rules.

Example:

- TODO [Dependency Work name](link/to/work/README.md): Dependency purpose from its Work contract.
    It provides API or mechanism that this Work consumes.
-->

## Children

<!-- List of direct child Works and their purpose. Use `STATUS [Work title](path/to/README.md): purpose.` Keep purpose text aligned with the child Work. See [Work lifecycle](workflow.md#lifecycle) for status, retention, and closure rules.

Example:

- TODO [Child Work name](child/README.md): Child purpose.
-->

## Links

<!-- List of other relevant links, e.g. to previously closed Investigation or Evaluation Works with one sentence description of why are they relevant to this Work. -->

## Additional context

<!-- Include useful context not covered above, including assumptions and open risks that affect the Work. Distinguish required contracts from provisional design. Keep shared context in the parent and local detail in the affected leaf; link instead of copying diagrams or API descriptions. -->
