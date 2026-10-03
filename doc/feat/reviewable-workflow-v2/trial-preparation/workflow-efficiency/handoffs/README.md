# Handoffs

Refine the orchestrator and delegated-agent handoff for bounded workflow
changes, then promote lasting guidance to
[orchestrator handoffs](../../../../../orchestrator.md) and the relevant WDR
process.

Assess bounded scope and review size and identify required dependencies and
shared edit surfaces before handoff, then start the executor promptly. The
reviewer may read remaining context during execution when that does not defer
necessary integration preflight. Coordinate shared owners, maps, indexes,
exact wording, formatter-valid snippets, and reserved WDR numbers where needed.
Consider integration effects. If overlap is unavoidable, sequence the Works
or name the remaining merge resolution; do not invent index categories or
ordering just to hide a conflict. The
[parent map](../README.md#works) tracks child order; deliver tree-orchestration
before handoffs when both edit the orchestrator owner.

Promote this ownership boundary to permanent
[orchestrator guidance](../../../../../orchestrator.md): the executor
implements, checks, and commits locally, then returns the artifact, concise
evidence, and blockers. In ordinary delegation, the executor does not push, open
a draft or ready PR, or edit its description. The owning orchestrator reviews
acceptance, scope, integration, and evidence, reuses reported evidence, and
sends one consolidated correction batch in the same session when needed. Before
publishing, assess maintainer review effort from the actual completed diff
against [Work scope and sizing](../../../../../workflow.md#scope-and-sizing). If
it exceeds the target, stop publication and partition the completed work into at
least two cohesive, independently reviewable child Work PRs within the target.
Define their contracts and dependencies, update the parent map, and get the
revised parent plan reviewed and merged before child delivery continues.
Preserve and reuse completed implementation and valid evidence, then
reassess each child diff. An explicit maintainer request may authorize a larger
review under Work scope and sizing.

After independent review and any needed correction loop pass, the orchestrator
pushes and opens a new PR ready for maintainer review; there is no draft-PR
phase. For amendments to existing PRs, the orchestrator reviews local changes
before pushing or editing the description. Ready requests maintainer review;
CI may still be pending. Readiness does not imply approval, and the maintainer
retains merge control.

Preserve worktree isolation and avoid repeating a full leaf review at each
tree layer. Aim for one coherent checked batch and focused commit per PR when
feasible, without a fixed commit-count rule. Rerun checks when changed scope,
failure, or an unresolved concern warrants it; do not repeat all checks at
every layer. Topology and review ownership follow the
[tree-orchestration outcome](../README.md) and this contract.

## Acceptance

- **AC-1 TODO** Handoff guidance coordinates dependencies and shared surfaces
  before execution, and defines the executor's local artifact/evidence/blocker
  return and the owning orchestrator's review, correction, push, and PR
  responsibilities.

  Validation: walk through a bounded new PR ready after independent review
  without a draft phase, an existing-PR amendment, and an oversized completed
  diff. For the oversized case, verify publication stops while retained work
  is partitioned and child diffs are reassessed; include a shared index
  dependency and deliver tree-orchestration first when it shares the owner.
- **AC-2 TODO** The owning orchestrator reuses the executor's acceptance
  evidence and sends one consolidated correction batch when needed; CI and human
  merge gates remain, with readiness not implying approval or completed CI.
  Validation: inspect one completed handoff and PR flow, checking evidence
  reuse, reruns only when a change, failure, or unresolved concern warrants
  them, and the ready-but-CI-pending state.
- **AC-3 TODO** Durable topology, handoff, and PR-ownership rules are promoted
  to their authoritative owners while preserving worktree isolation and
  maintainer control.
  Validation: follow the reading routes and review the updated owner
  guidance against the new-PR and amendment walkthroughs.
