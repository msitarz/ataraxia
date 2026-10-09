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
locations but must retain all fields and unexpected-field detection. Treat the
reviewed JSON as an opaque whole-value expectation; loading a repository-owned
static fixture does not make it external input. The adapter may inspect only
the path fields needed to normalize them, and must preserve every other field
so whole-value comparison detects missing or unexpected data. Do not add
duplicate schema validation or detailed models solely to type this fixture.
No product internals belong in acceptance support.

- **AC-1 TODO** Given shipped sample inputs, complete golden artifacts and typed
  adaptation preserve independently justified trade/result fields and path
  identity before the sample acceptance consumer runs.

  Validation: manually review derivation/data completeness and normalization;
  run strict/lint/doc/ac checks. Expected values are not command execution
  evidence; split golden/type work if the complete review exceeds five minutes.
