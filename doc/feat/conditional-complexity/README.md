# Conditional complexity guidance and prevention

## Purpose

Keep conditions readable through lasting engineering guidance and automatic
prevention at the normal Make/CI boundary.

## Goals

- Define guidance forbidding dense conditions while allowing clear, simple
  decisions.
- Adopt a supported complexipy candidate with evidence-based limits and any
  necessary complementary checks.
- Preserve affected behavior while repairing only violations necessary for
  enforcement.

## Non-Goals

- Introduce a generic lint framework, custom scanner, blanket exemptions, or
  suppressions.
- Authorize unrelated refactoring or a repository-wide source migration.
- Change PR #328 or require its merge before defining this Work.

## Mechanisms

- complexipy measures function-level cognitive complexity for automatic
  prevention.
- Ruff's
  [PLR0916](https://docs.astral.sh/ruff/rules/too-many-boolean-expressions/) is
  a candidate complementary per-condition check whose coverage remains to be
  established.
- Existing Make lint, setup, and required CI machinery provide the integration
  boundary.
- Two serial child Works separate the uncertain capability and threshold
  decision from production adoption.

### Shared guidance boundary

- Guidance covers `if`, `elif`, and `match` guards and exposes explicit
  validation boundaries and simple decisions.
- Clever compound short-circuit validation must not hide independent
  responsibilities or type prerequisites.
- Moving the same expression into a guard or comprehension, or extracting
  helpers merely to lower scores, is not a repair.
- Short independent guards may remain clearer than structural matching, and a
  Boolean operator alone does not make code unreadable.
- Precise measurable limits and reviewed exceptions remain investigation
  outcomes rather than assumptions.
- Guidance explains remaining manual review obligations without claiming that
  either metric guarantees readability.

### Shared preservation boundary

Repairs preserve the affected observable contract.

- Accepted and rejected inputs, relevant documented errors and exception causes,
  state invariants, safety guarantees, and necessary side-effect ordering remain
  unchanged.
- Validation order and branch organization may change when the observable
  contract is unchanged.
- Missing, wrong-type, Boolean, and negative seed identity values raise the
  relevant `ValueError` rather than an incidental comparison error, while
  nonnegative integer pairs pass.
- Repairs touching the surrounding validator preserve lifecycle and diagnostic
  rejection, arbitrary valid extension fields, and malformed persisted-state
  behavior.

## Acceptance criteria

### **AC-1 TODO** Guidance and prevention are integrated

Engineering guidance and functioning automatic prevention deliver the two
independently reviewed child outcomes.

- [Adoption AC-1](adopt/README.md#ac-1-todo-readable-condition-guidance)
  supplies guidance with useful allowed examples and truthful tool limits.
- [Adoption AC-2](adopt/README.md#ac-2-todo-blocking-make-and-ci-enforcement)
  supplies locked complexipy prevention through normal Make and required CI,
  including observed failing and passing behavior.
- [Adoption AC-3](adopt/README.md#ac-3-todo-compatible-bounded-repairs) supplies
  compatible bounded repairs where needed.
- A recommendation or capability-gap finding alone does not complete this
  outcome.

## Dependencies

- TODO [Validated core guidance](../validated-core/README.md) owns complete
  consumed-record validation, frozen values, pure functions, module
  responsibilities, and Protocol ports/adapters guidance; it must be integrated
  before adoption edits the shared engineering owner, while the capability
  investigation may proceed independently.

## Children

- TODO [Capability and threshold investigation](investigate/README.md): select a
  supported complexipy candidate and concrete complementary guidance/checks.
- TODO [Guidance and enforcement adoption](adopt/README.md): after independent
  review, lock the dependency, integrate prevention, and repair bounded
  violations.

## Links

- [Nested-exception guidance](../../engineering.md#code-style) is a delivered
  related manual guardrail rather than a dependency.
- [Algebraic data type Investigation](../algebraic-data-types/README.md)
  independently considers whether modeling improves the seed's broader lifecycle
  contract.

## Additional context

### Seed and planning baseline

The seed is the maintainer's
[comment on PR #328](https://github.com/msitarz/ataraxia/pull/328#discussion_r4272687628),
“need to have guidance on keeping complexity low (incl. complexipy)”. The frozen
[`_validate_record` at reviewed head 47779e4](https://github.com/msitarz/ataraxia/blob/47779e4dbf3df31d0c4ebcffd9d074ba493ccff3/script/sandbox.py#L465-L550)
validates lifecycle fields, failure diagnostics and destination identity before
separating owned fields from JSON-compatible extensions. Its identity condition
is:

```python
device, inode = values.get("destination_device"), values.get("destination_inode")
if (
    not isinstance(device, int)
    or isinstance(device, bool)
    or not isinstance(inode, int)
    or isinstance(inode, bool)
    or device < 0
    or inode < 0
):
    raise ValueError(f"malformed sandbox destination identity: {path}")
```

At planning baseline `cd3cb5e6a7abfbb91533c1b14be37b26ff05927a`,
[engineering conventions](../../engineering.md#code-style) prefer composition,
focused functions and guard clauses but have no explicit condition-complexity
ban. `uv.lock` pins Ruff 0.16.8; configuration enables SIM and PLR0915 statement
counts, with blocking lint and separate advisory counts through Make. complexipy
is absent. These are verified configuration facts, not capability experiments.

The complexipy
[usage guide](https://complexipy.com/usage-guide/) and
[refactoring rules](https://complexipy.com/refactoring-rules/) inform candidate
selection; they do not prove that an adopted version catches every dense
condition. Inspect the then-integrated source during execution because the
frozen seed does not establish the current repair inventory.

### Adoption uncertainty

A compatibility or enforcement gap, or an oversized repair inventory, pauses
adoption for maintainer steering or a concrete bounded split under the
[Work workflow](../../workflow.md#decisions-and-new-splits).
