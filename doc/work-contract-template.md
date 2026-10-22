# <Work name>

<!-- Replace the heading with the Work name and remove all instruction comments
before publishing. Keep only the relevant headings unless instruction comment says REQUIRED. Follow the shared [writing standard](README.md#writing) and use relative Markdown links. -->

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

## Inherited constraints

<!-- Optional. Link to the parent-owned constraints that apply to this Work and state any local constraints it adds.

A parent owns these shared constraints without predefining every signature:
- Concepts and invariants.
- Responsibilities, dependency direction, and effect limits.

Children inherit parent constraints without restating or weakening them.

For each non-functional requirement:
- State whether the local Work, an architectural integration, or the full system verifies it.
- Name the responsible verifier.
- Include workload and measurement conditions with a quantitative threshold.

A child can verify its local portion and complete its own outcome while the parent's system-level guarantee remains unverified. The parent verifies that guarantee across the integrated result.

Example: A parent requires p95 response time below 200 ms for a named request mix, concurrency, and deployment class. A child links to that constraint and verifies its route locally. The parent verifies the integrated service under the stated workload; the child's local completion does not claim system-level proof.
-->

## Visuals

<!-- For meaningful architecture, module relationships, interactions, or lifecycle changes, show proportionate before/after visuals using a suitable GitHub-supported Mermaid type. Tiny changes may use clear before/after prose.

Inspect current source or contracts and identify the verified before revision. Distinguish proposed additions, changes, and removals; label historical or illustrative designs, and correct the proposal when verified implementation differs. Show only affected context.

Check diagram accuracy against source and contracts. Use real Mermaid fences so `make doc-check` validates rendering syntax; passing rendering does not establish acceptance or GitHub/browser parity.
-->

## Acceptance criteria

<!-- List of acceptance criteria. REQUIRED.

- A Work owns one coherent outcome. Acceptance criteria state independently assessable conditions or behaviors that establish it; together, they fulfill the Work’s purpose and goals without a target number of criteria.
- Name each guarantee in the heading and start its criterion with a short sentence stating what becomes possible or changes when it is delivered.
- Include preconditions, expected results, relevant success, failure, refusal, preservation, and compatibility boundaries, and affected interfaces with useful signatures and types needed to determine completion.
- Keep multiple scenarios that establish the same guarantee together; use separate criteria for guarantees that can be assessed independently. A condition need not describe runtime behavior when the outcome is guidance, an Investigation, or an Evaluation.
- Given/When/Then is optional. Use it when it makes a condition easier to assess.
- State measurement thresholds and the workload and measurement conditions needed to interpret them when they define success.
- Put inherited constraints in the optional [Inherited constraints](#inherited-constraints) section, separately from local acceptance criteria; a child may add constraints but cannot weaken a parent's shared guarantees.
- Describe the delivered result rather than listing implementation tasks or instructions to the executor.
- Keep each requirement at one owner and link to it elsewhere; leave implementation details owned by child Works in those contracts.

Omit empty criterion subheadings.
-->

<!-- AC code outcome example:

### **AC-1 TODO** Executed purchases update cash and positions correctly

Applying a valid purchase fill produces a successor portfolio reflecting the purchased quantity, execution price, and fees.

#### Purchase without fees

- **Given** a portfolio with USD 1,000 cash and no positions.
- **When** a fill purchases two shares of XYZ at USD 100 each, with no fees.
- **Then** the successor portfolio contains USD 800 cash and two shares of XYZ.

#### Purchase with fees

- **Given** a portfolio with USD 1,000 cash and no positions.
- **When** a fill purchases two shares of XYZ at USD 100 each, with a total fee of USD 5.
- **Then** the successor portfolio contains USD 795 cash and two shares of XYZ.
-->

<!-- AC guidance outcome example:

### **AC-2 TODO** Complete record validation

Engineering guidance requires constructors to validate every consumed field and cross-field invariant before returning a domain value. Rejection may stop at the first error; successful construction guarantees all invariants hold. A compact example shows valid construction and rejection of an invalid field combination. If a child implements a particular constructor, it links to this shared invariant and states its own observable acceptance conditions separately.

For constraint inheritance and system-level verification examples, see [Inherited constraints](#inherited-constraints).
-->

## Dependencies

<!-- List of prerequisite Works, their purpose, and prerequisite explanation. Do **NOT** include direct children. Use `STATUS [Work title](path/to/README.md): purpose.` Ordinary guidance links have no Work status. Keep purpose text aligned with the linked Work. See [Work lifecycle](workflow.md#lifecycle) for status and retention rules.

Example:

- TODO [Dependency Work name](link/to/work/README.md): Dependency purpose from its Work contract.
    It provides API or mechanism that this Work consumes.
-->

## Children

<!-- List of direct child Works and their purpose. Use `STATUS [Work title](path/to/README.md): purpose.` Keep purpose text aligned with the child Work. See [Work lifecycle](workflow.md#lifecycle) for status and retention rules.

Example:

- TODO [Child Work name](child/README.md): Child purpose.
-->

## Links

<!-- List of other relevant links, e.g. to previously closed Investigation or Evaluation Works with one sentence description of why are they relevant to this Work. -->

## Additional context

<!-- Include useful context not covered above, including assumptions and open risks that affect the Work. Distinguish required contracts from provisional design. Keep shared context in the parent and local detail in the affected leaf; link instead of copying diagrams or API descriptions. -->
