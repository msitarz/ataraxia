# Conditional complexity guidance and prevention

Deliver lasting engineering guidance forbidding dense, complex conditions and
adopt complexipy through the normal Make/CI boundary. Guidance and functioning
automatic prevention are both required; a recommendation alone cannot complete
this Work. Use two serial leaves to separate the uncertain tool/threshold
decision from adoption.

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

The intended guidance applies to `if`, `elif` and `match` guards: expose
cohesive validation steps and simple decisions instead of Boolean expressions
that hide independent responsibilities, type prerequisites or evaluation order.
Moving the same expression into a guard, comprehension or helper per term is not
a repair. Short independent guards may remain clearer than structural matching.
Decide precise measurable limits and reviewed exceptions from examples during
the investigation; do not equate every Boolean operator with unreadable code.

complexipy measures function-level cognitive complexity. Its
[usage guide](https://complexipy.com/usage-guide/) and
[refactoring rules](https://complexipy.com/refactoring-rules/) inform candidate
selection; they do not prove that an adopted version catches every dense
condition. Evaluate Ruff's
[PLR0916](https://docs.astral.sh/ruff/rules/too-many-boolean-expressions/)
as a complementary per-condition check. The guidance must explain any remaining
manual review obligation without claiming either metric guarantees readability.

Preserve short-circuiting, evaluation order, error text and exception causes.
For the seed, missing, wrong-type, Boolean and negative identity values must
still raise the same ValueError without evaluating invalid comparisons;
nonnegative integer pairs pass. Preserve lifecycle/diagnostic rejection,
arbitrary valid extension fields, and malformed persisted-state behavior when
any repairs touch the surrounding validator. PR #328 remains independent:
inspect then-integrated source at execution; do not edit its branch or require
it to merge before defining this Work.

- TODO [Capability and threshold investigation](investigate/README.md): select
  a supported complexipy candidate and concrete complementary guidance/checks.
- TODO [Guidance and enforcement adoption](adopt/README.md): after independent
  review, lock the dependency, integrate prevention and repair bounded
  violations.

Reuse existing lint, setup and CI machinery. No generic lint framework, custom
scanner, blanket exemptions, suppressions or unrelated refactor is authorized.
A compatibility/enforcement gap or an oversized repair inventory pauses adoption
for maintainer steering or a concrete bounded split. The
[nested exception Work](../nested-exceptions/README.md) is related guardrail
planning, not a dependency. The independent
[algebraic data type Investigation](../algebraic-data-types/README.md) considers
whether modeling improves this seed's broader lifecycle contract.

- **AC-1 TODO** Both serial outcomes are independently reviewed and integrated:
  engineering guidance forbids dense conditions with useful allowed examples,
  and locked complexipy prevention runs through normal Make and required CI,
  with truthful limits and preserved affected behavior.

  Validation: review child evidence and lasting
  engineering/configuration/command owners; observe adopted failing and passing
  examples through Make, inspect CI integration and bounded repairs, and run
  documentation and acceptance checks.
