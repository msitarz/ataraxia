# Engineering judgment in review

## Purpose

Make agents apply engineering judgment during ordinary implementation review
without waiting for the maintainer to request simplification.

## Goals

- Give design judgment a focused guidance owner with a clear reading trigger.
- Make the existing orchestrator review apply that guidance to completed code
  and test changes, including corrections.
- Teach proportionate choices through compact questions and concrete examples.

## Non-Goals

- Implement the illustrative code changes or perform a repository-wide cleanup.
- Replace engineering, typing, testing, architecture, or scope rules with a
  second checklist.
- Add a mandatory reviewer agent, framework, scanner, formal benchmark,
  Evaluation deliverable, or review report or stamp.
- Require refactoring, comments, per-helper Protocols, or extra value variants
  merely to avoid `None`.

## Mechanisms

- `doc/engineering-review.md` owns the design judgment questions and examples
  used when reviewing code or tests.
- [Orchestrator guidance](../../orchestrator.md#review-and-return) owns the
  existing independent review and consolidated correction loop.
- Existing [Make reminders](../../../Makefile) route agents to the guidance at
  appropriate developer check and Work review boundaries.

## Before and after

At definition baseline `8de2f14a925f70d6a1d7c555fd833f5a3d8257ed`,
[engineering](../../engineering.md#structural-review) already calls for
structural review, and the orchestrator independently reviews completed
artifacts before publication; Make prints function-size, test-quality, and Work
sizing reminders.

The proposed change gives the judgment behind that review one focused owner
and connects existing reading and reminder routes directly to it, so a passing
check does not end review before unnecessary design complexity is considered.

## Acceptance criteria

### **AC-1 TODO** Focused and discoverable judgment guidance

Agents reviewing code or tests can reach `doc/engineering-review.md` directly
from applicable task and role guidance.

The owner states its code and test review trigger and provides a compact set of
questions about the smallest coherent design that satisfies the Work, repeated
state and interpretation, unnecessary checks and abstractions, and placement of
responsibilities. Questions link to the rules at their existing owners rather
than redefining them:

- Does the code state supported cases and domain intent directly, using
  meaningful `match` cases and shared rejection when the caller response is the
  same, while retaining short independent guards where clearer?
- Does it use standard Python or library semantics and protocols where they fit,
  normalize inputs and derive shared facts once, and reuse observations rather
  than repeat scans or interpretation?
- When iteration mixes traversal or context tracking with substantial per-item
  decisions, would a cohesive pure function with explicit inputs and results
  clarify those decisions while keeping cross-item state visible in the loop
  and using comprehensions only for independent items?
- Does the dynamic boundary produce a precise typed consumed contract, relying
  on documented SDK guarantees while distinguishing raw external ingress from
  trusted typed construction?
- Do constructors establish owned semantic and ownership invariants, with pure
  decisions separated from external adaptation, effects, and required live
  resource checks?
- Are internal invariant errors concise and external errors actionable, with
  expected filesystem failures handled at the owning adapter or reporting
  boundary while retaining actual domain, security, and ownership policies?
- Do focused tests observe meaningful behavior at the narrowest boundary, with
  higher-level tests proving integration obligations instead of duplicating
  complete lower-level oracles?

[AGENTS.md](../../../AGENTS.md), the
[documentation ownership table](../../README.md#owners), and applicable
engineering, testing, and role guidance give direct routes without an index
chain or duplicated checklist. Existing structural review guidance is integrated
at the appropriate owner instead of leaving competing explanations.

### **AC-2 TODO** Simplification is part of independent acceptance review

The orchestrator explicitly applies the judgment guidance before accepting a
completed implementation and before publishing the exact final revision,
including the final corrected revision even when automated checks pass.

The requirement is integrated into the existing
[completed-artifact review loop](../../orchestrator.md#review-and-return): the
orchestrator identifies bounded concrete corrections when warranted and
independently reviews their result before acceptance or publication. The review
may accept the implementation unchanged; there is no refactoring or comment
quota and no mandatory separate reviewer agent. Applicable review of the same
unchanged revision can satisfy both checkpoints without repeating the review.

An appropriate existing developer check reminder and `make work-review` point
directly to the judgment owner, preserving their existing purposes without
printing the reminder on every target. Reminders do not claim to verify taste;
checks or a harness can establish that a review step addressed the correct
revision, not that its judgment was good. No new evidence record is required.

Existing scope and stop rules, consolidated corrections, evidence reuse,
publication ownership, and maintainer review and merge authority remain in
force.

### **AC-3 TODO** Examples teach choices and their limits

A few compact before/after examples in the judgment owner explain why a simpler
design helps and when the original form remains appropriate.

The examples draw from the accepted Markdown range and Work selection changes
and the identified heading-boundary, typed CLI, and test ownership
opportunities:

- Range membership contrasts a custom `contains` method with `__contains__`
  and `in`, while explaining when a named method has different semantics.
- Work selection contrasts preflight probes and repeated interpretation with
  operation-first handling, supported file-type cases, and shared rejection,
  while preserving required containment and domain policies.
- Heading boundaries contrast repeated following-heading scans with shared
  derived facts, while criterion checking shows directly testable per-heading
  decisions with section membership and seen identifiers kept visible in the
  loop, without mandating a backward pass or another specific algorithm.
- Typed CLI and test examples contrast uncertainty propagated from a dynamic
  boundary and duplicate full oracles with a precise consumed contract and
  focused unit checks plus integration obligations, without prescribing an
  argparse class or test layout.

Examples distinguish historical approved changes from proposed improvements
and are checked against then-integrated source; identified opportunities are
not described as already implemented. They show meaningful alternatives, not
syntax-only rewrites or dense conditions relocated into guards; cohesive
extraction does not require a helper for every loop or extraction merely to
reduce statement counts. Contextual
stderr diagnostics illustrate useful external errors without establishing a
global command-output policy. Small examples may later help assess reviewer
usefulness without becoming a mandatory benchmark.

## Dependencies

- TODO [Validated core guidance](../validated-core/README.md) supplies the
  integrated validation, pure-core, adapter, and standard-protocol rules that
  the new owner links to before delivery.

## Links

- [Conditional complexity](../conditional-complexity/README.md) owns readable
  condition rules and measurable prevention, requiring coordination of shared
  engineering edits rather than dependency on its enforcement delivery.
- [Algebraic data type Investigation](../algebraic-data-types/README.md) owns
  the representation comparison and remains independent of this review lens.
- [Testing](../../testing.md) and [test ownership](../../test-ownership.md)
  retain test-boundary, expectation, and cleanup rules.
- [Change rules](../../change-rules.md), [architecture](../../architecture.md),
  and [Work workflow](../../workflow.md) retain repair, architectural, and scope
  authority.
- [WDR 14](../../wdr/0014-remove-mandatory-pr-records-for-manual-judgment.md)
  and [WDR 17](../../wdr/0017-review-local-artifacts-before-pr-publication.md)
  retain independent local review without a separate manual-review record.

## Additional context

Historical examples are available in commits `d01a316` (range membership),
`bfe5855` (typed constructors), `fedb722` (validation and filesystem failures),
and `1417db3` (Work selection dispatch). At the definition baseline,
[`_located_headings`](../../../script/work_check/rules.py) still scans later
headings separately for each boundary, and the
[CLI](../../../script/work_check/cli.py) consumes argparse results directly;
these are proposed example opportunities, not authorized production repairs.

The validated-core Work retains its Python 3.14 and deferred-annotation rule;
this Work does not copy every technical rule into review guidance. The change
elaborates the existing independent review responsibility rather than creating
a new delivery gate; any consequential workflow choice discovered during
delivery follows the [WDR workflow](../../wdr-workflow.md).
