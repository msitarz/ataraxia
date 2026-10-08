# Ataraxia testing boundaries

Replace patched product internals with real execution and strengthen independent
results while preserving trading, graph, resource, and user-visible contracts.

## Delivery map

- **DONE** Values: Bar, rolling windows, SMA, positions, and broker/account
  outcomes through public boundaries.

Values is delivered. Define the remaining groups in separate planning PRs, in
the order below, before implementation:

1. Input: `unit/test_provider.py` and `unit/test_source.py`; real temporary
   CSVs, complete Bars, contextual failures and resource state on exhaustion,
   error, and explicit close under ADRs 12 and 16.
2. Backtest/loading: `unit/test_backtest.py`, `integration/test_backtest.py`,
   and both `test_util.py` modules. First define named typed strategy fixtures
   and loader arrangements; then real sink/consumer selection, invalid results,
   exports and strategy errors under ADR 14. Remove internal doubles only after
   real replacement coverage preserves the corresponding cases.
3. CLI: `unit/test_cli.py` and `acceptance/test_crossover_sample.py`. Plan typed
   result fixtures before display/serialization consumers, argument-only units,
   then isolated real-command support and complete sample golden artifacts
   before success/failure flows. Preserve absent/unchanged output and exact
   exits; retain lower-level malformed-input coverage before reducing
   duplicates.
4. Compute: `unit/compute/test_graph.py`, `unit/compute/test_loop.py`, and
   `typecheck/compute_contracts.py`. Separate typed collaborator arrangements,
   graph/results/sharing, lifecycle, and binding reviews; retain real execution
   and precise positive/negative type contracts on their existing routes.

Paths above are relative to `test/ataraxia`; these are future planning scopes,
not implementation authorization. Split complete diffs, including supporting
fixtures and typing, for the five-minute review target. Serialize configuration,
helpers, golden artifacts and parent maps; merge dependency owners before their
consumers. Preserve cases/markers; use session-authorized concise slice
docstrings. No production repairs or property adoption belong here.

- **AC-1 TODO** Given completed values, input, backtest/loading, CLI and compute
  deliveries, retained product tests exercise real public boundaries with
  independent complete outcomes, precise failures and resource/lifecycle state,
  preserved case/marker provenance, and precise incremental strict typing of
  cleaned modules, helpers and fixtures without weakening product contracts.

  Validation: integrate independent child artifact/evidence reviews against
  architecture, relevant ADRs and testing guidance; run the complete product
  suite and strict type checks, and require latest-head full CI. Deferred groups
  remain unverified until their separately reviewed plans and deliveries are
  complete; planning readiness alone does not establish parent completion.
