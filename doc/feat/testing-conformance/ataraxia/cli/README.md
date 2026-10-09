# CLI testing conformance

## Delivery map

- **DONE** Reporting arrangements: typed broker-return inputs and complete
  independent serialization expectations for whole-value comparison.
- **DONE** Reporting units: real display totals and complete saved JSON use
  retained inputs, whole-value expectations and a disposable `out.json`.
- **DONE** Argument-only units: actual parser exits cover missing required
  options, unknown options and help before backtest work begins.
- **DONE** Command support: typed offline execution of the prepared shipped
  entry point with bounded capture and disposable process state, used by the
  real-command success and failure acceptance flows.
- **DONE** Sample golden artifacts: independently derived complete results and
  typed checkout-independent path/order adaptation; the success flow consumes
  these artifacts.
- **DONE** Success flow: the real prepared command asserts the exact report
  and complete normalized sample artifact while preserving its inputs.
- **DONE** Failure flows: real command refusals preserve malformed inputs and
  absent or prior output, including the empty-directory default-output case.

All seven CLI deliveries are integrated. Relative to `test/ataraxia`, strict
typing explicitly includes `cli_result_inputs.py`, `cli_sample_expected.py`,
`cli_process.py`, `acceptance/test_cli_success.py`,
`acceptance/test_crossover_sample.py`,
`unit/test_cli_reporting.py`, and `unit/test_cli_arguments.py`; the existing
negative type-check route is unchanged. Reviewed static JSON goldens are opaque
complete expectations; only actual output paths and unspecified shard order are
normalized. The prepared-process helper's offline isolated execution was
separately verified.

The original 16 case instances and identities remain: two reporting cases, the
sample success case, the moved `test_main_print_error_and_exit`, and twelve
malformed-input/output cases. Their historical row-first IDs remain
`no-shards-False`, `empty-file-False`, `header-only-False`, `bad-header-False`,
`bad-value-False`, `short-row-False`, `no-shards-True`, `empty-file-True`,
`header-only-True`, `bad-header-True`, `bad-value-True`, and `short-row-True`.
Four parser boundary cases were added; coverage markers remain on the delivered
CLI tests. The empty-directory acceptance case uses a copied strategy and
preserves the default `results.json` behavior.

- **AC-1 TODO** Given completed CLI deliveries, retained reporting/parser/user
  flows exercise real public behavior, complete independent artifacts and exact
  exits/failure state, preserving provenance and precise incremental typing
  without patched backtesting or weakened lower-level malformed-input coverage.

  Validation: integrate independent child reviews and case inventories; run all
  CLI modules, complete product suite and strict checks, and require latest-head
  full CI. Planning or fixture declarations alone do not verify this outcome.
