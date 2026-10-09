# Ataraxia testing boundaries

Replace patched product internals with real execution and strengthen independent
results while preserving trading, graph, resource, and user-visible contracts.

## Delivery map

- **DONE** Values: Bar, rolling windows, SMA, positions, and broker/account
  outcomes through public boundaries.
- **DONE** Input: real CSV/provider outcomes, source runner identity and
  context/resource forwarding. Explicit compute-generator lifecycle remains
  deferred to the Compute plan.
- **DONE** Backtest/loading: named typed modules, real results and
  export/error paths, and the distinct reordered-mapping regression.
- **TODO** [CLI](cli/README.md): typed reporting fixtures, argument-only units
  and isolated real-command success/failure artifacts.

Values, Input and Backtest/loading are delivered. Merge the CLI map before its
ordered deliveries. Define the remaining Compute group in a separate planning
PR before implementation:

1. Compute: `unit/compute/test_graph.py`, `unit/compute/test_loop.py`, and
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
