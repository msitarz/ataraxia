# Product package documentation

Plan ordered bounded leaves: compute; root overview; bar/broker/errors;
provider/source/feature; backtest/CLI/util. Cover src/ataraxia and compute,
including exports and reexport ownership. Relate graphs, runners, providers,
features and entry points to current architecture/ADRs without restating them
or documenting planned deployment as implemented. Root API/navigation edits
follow compute and remain serial.

Follow [parent scope, convention and delivery validation](../README.md).

- **AC-1 TODO** Product READMEs expose every direct owned module/subpackage and
  reusable public API with accurate implemented relationships and links to
  authoritative architecture/decisions and reexport owners.

  Validation: Merge concrete bounded contracts before edits; inspect
  exports/callers and main class operations, independently review
  architecture/API descriptions against code/ADRs and apply parent delivery
  checks.
