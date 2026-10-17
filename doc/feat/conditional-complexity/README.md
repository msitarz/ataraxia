# Conditional complexity prevention

## Purpose

Determine and integrate useful automatic condition-complexity prevention through
the normal Make/CI boundary.

## Goals

- Assess the latest stable complexipy release and establish evidence-based
  limits.
- Assess complementary Ruff coverage and truthful enforcement limits.
- Preserve affected supported contracts through bounded enforcement repairs.

## Non-Goals

- Own readable-condition or domain-modeling policy, which belongs to
  [integrated engineering guidance](../../engineering.md).
- Introduce a generic lint framework, custom scanner, blanket exemptions, or
  suppressions.
- Authorize unrelated refactoring, production migration, or changes to PR #328.

## Mechanisms

- The latest stable complexipy release is the function-level
  cognitive-complexity tool whose compatibility and coverage require
  documentation-first investigation.
- Ruff PLR0916 is a candidate complementary Boolean-expression check whose
  actual coverage must be observed.
- Existing Make lint, setup, locking, and required CI provide the integration
  boundary.
- The completed investigation establishes the reviewed tool capabilities;
  engineering guidance and normal Make/CI routes own the lasting policy and
  enforcement.

### Shared preservation boundary

Repairs preserve the actual affected supported contracts at the then-integrated
baseline: accepted and rejected inputs, relevant documented errors and causes,
state invariants, safety, persistence compatibility, and essential effect
ordering. Boundary checks remain where they establish owned input or live
resource guarantees. Incidental defensive checks, validation order, and branch
organization need not remain when these contracts are preserved.

## Acceptance criteria

### **AC-1 DONE** Guidance and prevention are integrated

Integrated readable-condition policy and the independently reviewed tooling
outcomes provide useful automatic prevention with truthful limits.

- [Readable-decision guidance](../../engineering.md#code-style)
  supplies readable-condition policy without duplicating it in this Work.
- [Adoption AC-1](https://github.com/msitarz/ataraxia/blob/0fc008156c196d66c56c28c27233a35aec89ba42/doc/feat/conditional-complexity/adopt/README.md#ac-1-done-truthful-tool-guidance)
  supplied integration guidance explaining supported capabilities and remaining
  judgment.
- [Adoption AC-2](https://github.com/msitarz/ataraxia/blob/0fc008156c196d66c56c28c27233a35aec89ba42/doc/feat/conditional-complexity/adopt/README.md#ac-2-done-blocking-make-and-ci-enforcement)
  supplied the locked reviewed tool through normal Make and required CI.
- [Adoption AC-3](https://github.com/msitarz/ataraxia/blob/0fc008156c196d66c56c28c27233a35aec89ba42/doc/feat/conditional-complexity/adopt/README.md#ac-3-done-compatible-bounded-repairs)
  supplied compatible repairs where necessary.
- A recommendation or capability-gap finding alone does not complete prevention.

## Dependencies

- DONE [Integrated engineering guidance](../../engineering.md) owns validation,
  modeling, pure decisions, ports, effects, and readable-condition policy;
  adoption consumes these delivered rules, while investigation may proceed
  independently.

## Children

- DONE
  [Capability and threshold investigation](https://github.com/msitarz/ataraxia/blob/2416d974065d9086f8123baeae76a3c95057598d/doc/feat/conditional-complexity/investigate/findings.md):
  documentation-first assessment of Complexipy 8.0.1 recommends inclusive limit
  15 with Ruff PLR0916 at maximum five.
- DONE
  [Tooling adoption](https://github.com/msitarz/ataraxia/blob/0fc008156c196d66c56c28c27233a35aec89ba42/doc/feat/conditional-complexity/adopt/README.md):
  integrate the reviewed selection and truthful limits, with bounded repairs
  after both prerequisites.

## Additional context

The historical prompt was a
[PR #328 comment](https://github.com/msitarz/ataraxia/pull/328#discussion_r4272687628)
asking for lower complexity, including complexipy. That sandbox example is
context rather than a frozen acceptance or error contract for future repairs.
The reviewed investigation recommends an inclusive threshold of 15 with Ruff
PLR0916 at its default maximum of five. Unresolved capability gaps require
steering; integration or repairs exceeding a short review sitting require a
reviewed bounded split under
[Work workflow](../../workflow.md#decisions-and-new-splits).
