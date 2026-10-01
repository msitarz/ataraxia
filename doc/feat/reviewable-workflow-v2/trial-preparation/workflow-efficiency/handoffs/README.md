# Handoffs

Refine the orchestrator and delegated-agent handoff for bounded workflow
changes, then promote lasting guidance to
[orchestrator handoffs](../../../../../orchestrator.md) and the relevant WDR
process.

Assess bounded scope and review size, then start the executor promptly. Before
handoff, identify dependencies, shared owners, maps, and indexes; coordinate
exact shared wording, formatter-valid snippets, and reserved WDR numbers where
needed. Consider integration effects and expected shared edits. If overlap is
unavoidable, sequence the Works or name the remaining merge resolution; do not
invent index categories or ordering just to hide a conflict.

Promote this ownership boundary to permanent
[orchestrator guidance](../../../../../orchestrator.md): Luna implements,
checks, and commits locally, then returns the artifact, concise evidence, and
blockers. In ordinary delegation, Luna does not push, open a draft or ready
PR, or edit its description. The owning orchestrator reviews acceptance,
scope, integration, and evidence, reuses reported checks, and sends one
consolidated correction batch in the same session when needed. Only after that
review does the orchestrator push, open or update the PR, mark it ready for
maintainer review, and maintain its description and metadata. For amendments
to existing PRs, the orchestrator reviews local changes before pushing or
editing the description. Ready
requests maintainer review; CI may still be pending. Readiness does not imply
approval, and the maintainer retains merge control.

Preserve worktree isolation and avoid repeating a full leaf review at each
tree layer. Aim for one coherent checked batch and focused commit per PR when
feasible, without a fixed commit-count rule. Rerun checks when changed scope,
failure, or an unresolved concern warrants it; do not repeat full validation at
every layer. Topology and review ownership follow the
[tree-orchestration outcome](../README.md) and this contract.

## Acceptance

- **AC-1 TODO** Handoff guidance coordinates dependencies and shared surfaces
  before execution, and defines Luna's local artifact/evidence/blocker return
  and the owning orchestrator's review, correction, push, and PR
  responsibilities.
  Verification: walk through a bounded new PR and an
  existing-PR amendment, including a shared index dependency, from handoff
  through maintainer review.
- **AC-2 TODO** The owning orchestrator reuses Luna's acceptance evidence and
  sends one consolidated correction batch when needed; CI and human merge gates
  remain, with readiness not implying approval or completed CI.
  Verification: inspect one completed handoff and PR flow, checking evidence
  reuse, reruns after changes only, and the ready-but-CI-pending state.
- **AC-3 TODO** Durable topology, handoff, and PR-ownership rules are promoted
  to their authoritative owners while preserving worktree isolation and
  maintainer control.
  Verification: follow the reading routes and review the updated owner
  guidance against the new-PR and amendment walkthroughs.
