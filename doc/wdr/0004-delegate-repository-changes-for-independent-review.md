# 4. Delegate repository changes for independent review

Date: 2026-10-01

## Status

Accepted

## Context

Repository changes need bounded execution while the orchestrator retains
independent review and the maintainer retains the final human decision.

## Decision

Delegate repository changes to Luna at low reasoning effort; higher effort
requires explicit maintainer approval. Luna executes its bounded task directly
without recursively delegating it. The orchestrator owns planning and review.
If Luna is unavailable, report that and wait rather than silently switching
agents or implementing the change as fallback.

## Consequences

Implementation and review remain separate responsibilities, with the
maintainer's manual review and merge gates intact. See
[orchestrator handoffs](../orchestrator.md) and
[PR #81](https://github.com/msitarz/ataraxia/pull/81).
