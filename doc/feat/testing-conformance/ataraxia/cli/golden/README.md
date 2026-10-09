# Complete independent sample artifacts

After command support, own `fixtures/cli/crossover_expected.json`, its concise
trade derivation `crossover_expected.md`, and typed `cli_sample_expected.py`
with its strict include. Derive complete accounts/Positions/Bars and strategy/
shard paths from shipped example and sample data under architecture/ADR 13/14.
Review golden values independently; never generate expectations by running CLI,
broker or strategy implementation and copying their output.

Preserve two shards, accounts 10/0 and 30/0, closed trades sell64926/+30,
buy64608/-20 and buy64480/+30, and empty open lists. Add every previously
omitted entry/closing field, bar timestamp/OHLCV, stop/target and exact path
identity. Path substitution or shard-order normalization may adapt checkout
locations but must retain all fields and unexpected-field detection. Validate
external JSON honestly; no imports of product internals into acceptance support
or broad helper result types hiding unknown data.

- **AC-1 TODO** Given shipped sample inputs, complete golden artifacts and typed
  adaptation preserve independently justified trade/result fields and path
  identity before the sample acceptance consumer runs.

  Validation: manually review derivation/data completeness and normalization;
  run strict/lint/doc/ac checks. Expected values are not command execution
  evidence; split golden/type work if the complete review exceeds five minutes.
