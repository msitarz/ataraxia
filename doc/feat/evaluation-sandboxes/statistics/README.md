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

A compact comparison records each serious candidate's checked fit, pros/cons and
uncertainty for exact session filtering, headless JSON/Python access, temporary
custom-state discovery, input, cached input, output and reasoning tokens,
deduplication across resumes and version limits. Native CLI limitations and the
possibility that no candidate fits stay explicit; prior third-party
documentation reading established no tokenuse fit or adoption.

Cost-estimate fit distinguishes requested from observed model/tier, pricing
source/version/date, fallback-model pricing, cache/reasoning category overlap
and unavailable categories. Bounded manually traced declared event/session
records and primary references ground available values and provenance.
Absent/unsupported data, unresolved category overlap and unsupported pricing
remain unknown; subscription billing is never inferred.

### **AC-2 TODO** Recommend reporting from tool-outcome evidence

The recommendation establishes successful/failed tool coverage or its precise
gaps and feasible report inputs from representative available tool outcomes and
initial/resumed identities. It distinguishes tool failure from command exit,
expected denial probes from agent mistakes, and model calls from tool calls and
tool process sessions. Token coverage alone cannot select a method.

The result recommends a fitting existing option, bounded manual/native reporting
or no integration with reasons; it does not install or integrate a report tool.
Missing custom collection machinery requires a new reviewed contract before
adoption.

## Data and scope limits

Before checking data, the comparison file declares exact existing owned
privacy-safe files/session UUIDs, provenance, permitted fields, candidate
versions and bounded manual methods. Only primary documentation/source and those
controlled records are consumed. Missing suitable data yields uncertainty, not
wider access. No model runs, unrelated host-session/auth reads, global usage
ingestion, mandatory dataset schema or new telemetry framework is included.
