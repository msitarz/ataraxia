# Engineering judgment in review

Read this when changing or reviewing code or tests. Apply these questions as
you make small changes and when you review the completed result:

- Does the change implement the Work's smallest coherent design?
- Can repeated state or interpretation be derived once?
- Do new types with the same meaning belong together?
- For distinct variants with shared fields or behavior, would a shared base or
  helper clarify their common contract, including for diagnostics?
- Do checks and abstractions earn their complexity?
- Do types, behavior, tests, and effects live with the responsibility that
  owns them?

Review may accept the design unchanged; no refactor or comment quota applies.

- Keep intentional overlap when it is clearer.
- Explain intentional overlap in the PR when it is clearer.
- Move code or extract a helper only when that clarifies its responsibility
  and resulting contract.
- Review the actual data flow through composition, including dependency-key to
  runner-parameter mappings, execution order, and effect ownership.

Static typing may miss incorrect dynamic graph mappings.

- Follow representative inputs through the wired path.
- Verify the resulting behavior at its owning boundary.

## Focused rule review

Focused rule review is optional. When using focused rule review:

- Assess each named engineering rule against one identified, immutable revision.

Return one judgment for that rule:

- `PASS`: adequate context supports that the change does not violate this rule.
- `VIOLATION`: evidence shows that this rule is broken.
- `NOT_APPLICABLE`: this rule does not apply to the change; state why.
- `UNCERTAIN`: context is missing or ambiguity remains; do not invent a pass or
  violation.

Use the following context and finding rules:

- Include the old and new function when relevant to the rule.
- Include the rule-specific caller, type, and module context needed to make the
  judgment.
- Support each finding with concrete evidence.
- Explain each finding's consequence.
- Keep findings separate from suggestions for possible improvement.
- Have the responsible owner deduplicate overlapping findings.
- Have the responsible owner judge conflicts between rules and rule
  applicability.
- Use focused findings to support the owner's judgment of the whole change.
- Keep architecture review responsible for intent, ownership, and dependencies.
- Keep engineering review responsible for implementation quality.
- Do not treat focused judgments as a replacement for substantive whole-change
  review.
- Do not set a finding quota when the reviewed change is sound.
- Do not require refactoring when the reviewed change is sound.

## Three contrasts

These examples distinguish accepted history from possible future choices.
They illustrate judgment; they do not require rewriting similar code.

### Use standard Python semantics

**Historical changes** (`1d43b18`, `d01a316`): before, `TextBlock` repeated a
set of literal kinds and `SourceLocation` exposed `.contains(child)`; after,
the current [Markdown model](../script/markdown/model.py) derives literal kinds
from `TextKind` and expresses range membership as `child in parent`. This
removes a second inventory and uses Python's membership protocol. Keep a named
operation when its domain meaning differs from ordinary membership.

### Select one case or collect independent findings

**Historical changes** (`1417db3`, `561816e`): before, Work selection used
separate file-kind checks; the current
[discovery code](../script/work_check/discovery.py) uses `match` because a path
has one mode. The current [Work rules](../script/work_check/rules.py) instead
collect independent criterion failures so one malformed declaration can report
more than one finding. Checks that need parsed fields remain behind a successful
format match. Use exclusive dispatch for one-of-many cases; use clear guards or
a small local collection when independent constraints can accumulate. Keep
prerequisites visible and predicates readable.

### Attempt the operation and handle its expected failure

**Historical change** (`fedb722`): Work discovery removed a separate symlink
probe and local resolver wrapper; its current owner resolves the selection and
translates expected filesystem errors, while contract reads translate failures
at the read site. A possible future adapter can likewise attempt a read or
write and handle its expected failure where that operation is owned. Preserve
root containment, authorization, ownership, and resource lifecycle checks that
the operation alone cannot establish; state-dependent checks may need to be
atomic with the operation.

Use [engineering conventions](engineering.md) for the lasting rules on
boundaries, modeling, pure decisions, ports, effects, readable conditions, and
type precision. [Testing](testing.md) owns test policy and observation
boundaries; [test ownership](test-ownership.md) owns cleanup decisions.
