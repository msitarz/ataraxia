# 4. Delegate repository changes for independent review

Date: 2026-10-01

## Status

Accepted

Amended by
[12. Orchestrate Work trees by responsibility](0012-orchestrate-work-trees-by-responsibility.md).

Amended by
[13. Use Sol-low for all leaves](0013-use-sol-low-for-all-leaves.md).

## Context

Repository changes need bounded execution while the orchestrator retains
independent review and the maintainer retains the final human decision. Having
the orchestrator make each change directly avoids a handoff but combines
execution and review.

## Decision

Delegate repository changes to Luna at low reasoning effort; higher effort
requires explicit maintainer approval. Luna executes its bounded task directly
without recursively delegating it. The orchestrator owns planning and review.
If Luna is unavailable, report that and wait rather than silently switching
agents or implementing the change as fallback.

## Consequences

Changes and review remain separate responsibilities, with the
maintainer's manual review and merge gates intact. See
[orchestrator handoffs](../orchestrator.md) and
[PR #81](https://github.com/msitarz/ataraxia/pull/81).
