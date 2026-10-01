# Handoff recovery

Make completed, blocked, interrupted, and stalled delegated handoffs actionable
without continuous polling or loss of useful evidence.

[Orchestrator guidance](../../../../orchestrator.md) asks for changes and
evidence and directs corrections to the same Luna session, but gives no minimum
return contents or recovery procedure when that session ends.

Extend that owner with a concise return contract: branch or revision, outcome,
acceptance evidence, checks and results, unresolved criteria, and blockers.
Define how a fresh session recovers scope and current state from the Work,
branch or PR, and available evidence. Require delegated scope growth to be
reported before implementation expands. Define an observable stopping condition
for repeated unsuccessful corrections and the steering needed to resume.

## Acceptance

- **AC-1 TODO** A return identifies the reviewable artifact and sufficient
  evidence for the orchestrator to distinguish completion from a blocker.
  Verification: review example successful and blocked returns against the
  required contents, including unrun checks and unresolved criteria.
- **AC-2 TODO** After cancellation or loss of a Luna session, the recovery
  procedure identifies retained changes, reusable evidence, and remaining work
  before a replacement session continues; uncertainty is surfaced.
  Verification: walk through recovery from a partial implementation and from
  completed changes awaiting review using a fresh-session context.
- **AC-3 TODO** Scope expansion and stalled correction loops have explicit
  stopping and escalation behavior, preserving approval for a different agent
  or higher reasoning effort.
  Verification: walk through an out-of-scope discovery, repeated failure to
  resolve a finding, and an unavailable delegated agent; review any qualifying
  WDR proposal with the maintainer.

Keep ordinary consolidated review and evidence reuse. The return and recovery
information belongs in existing handoff responses and PRs.
