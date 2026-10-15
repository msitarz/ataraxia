# Session statistics Investigation

## Purpose

Determine which existing method can report declared managed Codex sessions
accurately without widening access to host data.

## Goals

- Compare tokenuse, suitable Python alternatives and native CLI JSON against
  session-scoped needs.
- Identify token, cost-estimate and tool-outcome support with explicit
  uncertainty.
- Recommend a fitting method or a bounded no-integration outcome without
  adoption.

## Mechanisms

- [tokenuse source](https://github.com/russmckendrick/tokenuse) and its
  [Codex documentation](https://tokenuse.app/docs/development/tools/codex/)
  supply one existing reporting candidate.
- Suitable Python alternatives supply other existing headless reporting
  candidates.
- [Native CLI JSON](https://learn.chatgpt.com/docs/non-interactive-mode)
  supplies the baseline for comparison with session records.

## Acceptance criteria

### **AC-1 TODO** Compare session, token and cost-estimate fit

The comparison records each serious candidate's checked fit, tradeoffs and
uncertainty.

- Available values/provenance follow primary references and bounded manual
  traces of declared event/session records.
- Session criteria cover exact filtering, headless JSON/Python access, temporary
  custom-state discovery, resume deduplication and version limits.
- Token criteria cover input, cached input, output and reasoning categories,
  including unresolved overlap and unavailable data.
- Cost-estimate fit records requested/observed model and tier, pricing
  source/version/date, fallback pricing and category semantics.
- Absent/unsupported data, unresolved overlap and unsupported pricing stay
  unknown without inferred subscription billing, and native CLI limits or no
  fitting candidate stay explicit.

Prior third-party documentation reading establishes no tokenuse fit or adoption.

### **AC-2 TODO** Recommend reporting from tool-outcome evidence

The recommendation chooses a fitting existing method, bounded manual/native
reporting or no integration with reasons.

- Representative available tool outcomes and initial/resumed identities
  establish successful/failed coverage, precise gaps and feasible inputs.
- Tool failure differs from command exit, expected denial from agent mistakes,
  and model calls from tool calls and tool process sessions.
- Token coverage alone cannot select a method, and the result installs or
  integrates no tool.
- Missing custom collection machinery requires a new reviewed contract before
  adoption.

## Data and scope limits

Before checking data, the comparison file declares exact existing owned
privacy-safe files/session UUIDs, provenance, permitted fields, candidate
versions and bounded manual methods. Only primary documentation/source and those
controlled records are consumed. Missing suitable data yields uncertainty, not
wider access. No model runs, unrelated host-session/auth reads, global usage
ingestion, mandatory dataset schema or new telemetry framework is included.
