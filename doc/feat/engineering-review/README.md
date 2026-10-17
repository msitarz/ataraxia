# Engineering judgment in review

## Purpose

Make agents apply engineering judgment during implementation and independent
review without waiting for the maintainer to request simplification.

## Goals

- Give design judgment a focused owner and direct reading routes.
- Apply judgment in executor self-review and existing orchestrator review.
- Teach proportionate choices through three compact contrasts.

## Non-Goals

- Implement illustrative code changes or perform a repository-wide cleanup.
- Create a second engineering or testing policy, reviewer agent, harness,
  report, or delivery gate.
- Force `match`, variants, tables, wrappers, or a refactoring or comment quota.

## Mechanisms

- `doc/engineering-review.md` owns compact judgment questions and examples.
- Existing task and role routes and Make reminders make that owner discoverable.
- [Orchestrator guidance](../../orchestrator.md#review-and-return) owns
  independent review and consolidated corrections.

## Visuals

At verified definition baseline `bce76e5`, structural and independent review
responsibilities already exist. The proposed change gives judgment a focused
owner; executor self-review before handoff and orchestrator review of the
completed artifact use it through existing routes.

## Acceptance criteria

### **AC-1 DONE** Focused and discoverable judgment guidance

Agents changing or reviewing code or tests can reach the judgment owner directly
from applicable task and role guidance.

The owner asks compact questions about the smallest coherent design satisfying
the Work, repeated state and interpretation, unnecessary checks and
abstractions, and placement of responsibilities. It links to
[integrated engineering guidance](../../engineering.md) for boundary, modeling,
pure-decision, port, effect, and readable-condition rules rather than defining
them again. Integrated engineering guidance is the lasting rules owner.
[Testing](../../testing.md) and
[test ownership](../../test-ownership.md) retain test policy, meaningful
observation boundaries, and cleanup authority.

[AGENTS.md](../../../AGENTS.md), the
[documentation ownership table](../../README.md#owners), and applicable
engineering, testing, and role guidance give direct routes. Existing structural
review guidance is integrated at its owner without a competing checklist or
index chain.

### **AC-2 DONE** Judgment is applied before handoff and acceptance

Executors apply the judgment guidance in self-review before handoff, and the
orchestrator applies it independently before accepting completed implementation
and publishing the exact final revision, including corrections.

Passing checks do not end design judgment. The existing completed-artifact
review loop identifies bounded concrete corrections when warranted and reviews
their result independently. Review may accept the design unchanged, and
applicable review of the same unchanged revision can satisfy both orchestrator
checkpoints without repetition.

An appropriate existing developer-check reminder and `make work-review` point
directly to the owner while preserving their existing purposes. Reminders do
not certify judgment and require no new agent, harness, report, or gate.
Existing scope and stop rules, consolidated corrections, evidence reuse,
publication ownership, and maintainer review and merge authority remain intact.

### **AC-3 TODO** Examples teach choices and their limits

Three compact before/after contrasts explain why a simpler design helps and when
the original form remains appropriate.

- Standard Python semantics contrast custom interpretation with a natural
  protocol or library operation, deriving shared facts once where useful and
  retaining named operations when their meaning differs.
- Exclusive dispatch contrasts one-case selection with independent constraints,
  showing accumulated findings through simple guards or a small local diagnostic
  collection when needed, without hiding type prerequisites or dense predicates.
- Operation-first handling contrasts repeated preflight probes with an attempted
  operation and expected failure handling at its owner, preserving essential
  containment, ownership, security, and lifecycle policies.

Accepted Markdown and Work-check changes provide illustrative sources rather
than templates. Examples are checked against then-integrated source and
distinguish historical changes from proposed opportunities. They teach coherent
decisions rather than syntax-only rewrites, helper extraction to game counts,
or direct private-helper testing. Testing examples, if needed, link to their
existing owners rather than introducing duplicate oracles or a new test policy.

## Dependencies

- DONE [Integrated engineering guidance](../../engineering.md) supplies
  boundary, modeling, pure-decision, port, effect, and readable-condition rules
  for the review owner to link to.

## Links

- [Conditional complexity](../conditional-complexity/README.md) owns tooling
  investigation and enforcement independently of this judgment guidance.
- [Change rules](../../change-rules.md), [architecture](../../architecture.md),
  and [Work workflow](../../workflow.md) retain repair, architecture, and scope
  authority.
- [WDR 14](../../wdr/0014-remove-mandatory-pr-records-for-manual-judgment.md)
  and [WDR 17](../../wdr/0017-review-local-artifacts-before-pr-publication.md)
  retain independent local review without a separate manual-review record.
