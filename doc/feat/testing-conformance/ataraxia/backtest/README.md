# Backtest and loading conformance

## Delivery map

- **DONE** Valid arrangements: typed strategy and loader fixtures, a retained
  literal CSV shard, and independent complete result observations in
  `test/ataraxia/fixtures/backtest/` and `test/ataraxia/backtest_support.py`.
- **DONE** Module loading: retained utility tests cover the exact missing-module
  refusal and loading the copied six-field Bar fixture through `import_file`.
- **DONE** Real results: shard and directory backtests compare complete
  resolved-path snapshots and exercise direct-sink and broker-consumer results.
- **DONE** Invalid arrangements: nine named, strictly checked fixtures cover
  invalid exports, module/construction errors and invalid result variants under
  `test/ataraxia/fixtures/backtest/`; support keeps invalid fixture names
  separate from the valid strategy type.
- **DONE** Export and strategy failures: seven retained real-loader cases
  preserve absent/invalid exports, contextual causes and module/construction
  `AttributeError` outcomes in the typed integration tests.
- **DONE** Result/input refusals: two invalid selected results, a header-only
  shard and a missing directory retain exact contextual errors and input state
  through the real backtest and directory boundaries.
- **TODO** [Mapping-order selection](ordering/README.md): retain the distinct
  consumer-before-sink mapping regression through a justified narrow adapter.

Merge this map before implementation; deliver leaves in listed order. All paths
below are relative to `test/ataraxia`. Serialize shared includes, arrangements,
legacy subsets and maps. Every changed module/helper/executable fixture is
precisely typed and explicitly normal strict checked; untouched remainders are
not adopted by implication. Preserve case identities/markers and use concise
slice docstrings, Given/When/Then and independent complete expectations.

Fixture owners precede consumers; no generated substantial source, `.replace`
variants or forward fixture dependencies. No production repair, property
adoption, broad types/ignores/casts to hide mismatch, or blanket conftest
cleanup. Split full fixture/type/test changes before exceeding five-minute
review. Each leaf runs focused cases and affected legacy remainders, strict
typing, lint/format and doc/ac checks; latest-head full CI remains the merge
gate.

Ordinary real compute puts its selected graph root last. Natural consumer
execution therefore cannot replace the reordered-mapping claim. Retain that
regression separately; adapter feasibility/type constraints remain unverified
until its leaf delivers. Do not remove it or call it real ordering coverage.

- **AC-1 TODO** Given delivered leaves, retained loading/backtest cases observe
  real modules/graphs, complete independent results and contextual failures,
  preserve the distinct mapping-order selection regression and provenance, and
  precisely type cleaned tests and executable fixtures.

  Validation: integrate independent child reviews and old/new inventories; run
  all loading/backtest modules, complete product suite and strict checks, and
  require latest-head full CI. Unresolved ordering constraints prevent
  completion.
