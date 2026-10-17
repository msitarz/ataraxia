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
- Separate investigation and adoption children distinguish uncertain feasibility
  from production integration.

### Shared preservation boundary

Repairs preserve the actual affected supported contracts at the then-integrated
baseline: accepted and rejected inputs, relevant documented errors and causes,
state invariants, safety, persistence compatibility, and essential effect
ordering. Boundary checks remain where they establish owned input or live
resource guarantees. Incidental defensive checks, validation order, and branch
organization need not remain when these contracts are preserved.

## Acceptance criteria

### **AC-1 TODO** Guidance and prevention are integrated

Integrated readable-condition policy and the independently reviewed tooling
outcomes provide useful automatic prevention with truthful limits.

- [Readable-decision guidance](../../engineering.md#code-style)
  supplies readable-condition policy without duplicating it in this Work.
- [Adoption AC-1](adopt/README.md#ac-1-todo-truthful-tool-guidance) supplies
  integration guidance explaining supported capabilities and remaining judgment.
- [Adoption AC-2](adopt/README.md#ac-2-todo-blocking-make-and-ci-enforcement)
  supplies the locked reviewed tool through normal Make and required CI.
- [Adoption AC-3](adopt/README.md#ac-3-todo-compatible-bounded-repairs) supplies
  compatible repairs where necessary.
- A recommendation or capability-gap finding alone does not complete prevention.

## Dependencies

- DONE [Integrated engineering guidance](../../engineering.md) owns validation,
  modeling, pure decisions, ports, effects, and readable-condition policy;
  adoption consumes these delivered rules, while investigation may proceed
  independently.

## Children

- TODO [Capability and threshold investigation](investigate/README.md):
  establish latest-release capability, justified limits, repair scope, and
  integration feasibility.
- TODO [Tooling adoption](adopt/README.md): integrate the reviewed selection and
  truthful limits, with bounded repairs after both prerequisites.

## Additional context

The historical prompt was a
[PR #328 comment](https://github.com/msitarz/ataraxia/pull/328#discussion_r4272687628)
asking for lower complexity, including complexipy. That sandbox example is
context rather than a frozen acceptance or error contract for future repairs.
The investigation examines then-integrated source using the latest stable
complexipy release at execution start; no threshold or complementary coverage
has yet been established. A capability gap or repair
inventory beyond a short review sitting requires steering or a reviewed bounded
split under [Work workflow](../../workflow.md#decisions-and-new-splits).
