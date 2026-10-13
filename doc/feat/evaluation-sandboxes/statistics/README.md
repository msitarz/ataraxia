# Session statistics Investigation

Which existing method can accurately report only declared managed Codex sessions
through headless JSON or a suitable Python API, including custom temporary
state, token accounting, API-equivalent cost estimates and successful/failed
tools? After
[reconciliation](../reconciliation/README.md), compare
[tokenuse source](https://github.com/russmckendrick/tokenuse), its
[Codex documentation](https://tokenuse.app/docs/development/tools/codex/),
suitable Python alternatives and the
[native CLI JSON baseline](https://learn.chatgpt.com/docs/non-interactive-mode).
Prior third-party documentation reading established no tokenuse fit or adoption.

Use primary documentation/source and controlled existing owned privacy-safe
session data only. Before checking data, declare exact files/session UUIDs,
provenance, permitted fields, candidate versions and bounded manual methods in
the comparison file. No model runs, unrelated host-session/auth reads, global
usage ingestion, mandatory dataset schema or new telemetry framework. If
suitable data is absent, report uncertainty rather than widening access. The
result is a recommendation, not installation or report integration.

## Acceptance

- **AC-1 TODO** A compact comparison records each serious candidate's checked
  fit, pros/cons and remaining uncertainty for exact session filtering, headless
  JSON/Python access, temporary custom-state discovery, input/cached/
  output/reasoning tokens, deduplication across resumes and version limits.
  Native CLI limitations and the possibility that no candidate fits are
  explicit. Assess cost-estimate fit: requested versus observed model and tier,
  pricing source/version/date, fallback-model pricing, cache/reasoning category
  overlap and unavailable categories. Unsupported pricing remains unknown;
  subscription billing is not inferred.

  Validation: independent review of primary references and declared-data checks;
  compare reported values with bounded manually traced events/session records
  without collecting unrelated sessions. Record absent/unsupported data as
  unknown, including any overlap between reasoning and output token totals.
  Trace available model/tier and pricing provenance, including fallback cases,
  against primary references; distinguish checked estimate support from gaps.
- **AC-2 TODO** The recommendation establishes successful/failed tool coverage
  or its precise gaps, distinguishes tool failure from command exit and expected
  denial probes from agent mistakes, and defines feasible report inputs without
  selecting a tool on token coverage alone.

  Validation: independently trace representative available tool outcomes and
  initial/resumed session identities in the declared data; distinguish model
  calls, tool calls and tool process sessions. Recommend a fitting option,
  bounded manual/native reporting, or no integration with reasons. Require a
  new reviewed contract before adopting any missing custom collection machinery.
