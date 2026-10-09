# Real result and input refusals

After export failures, own new `integration/test_backtest_refusals.py`, the
remaining missing-directory case in `unit/test_backtest.py`, and their strict
includes. Replace unit's two `requires_broker_result` cases with real selected
fixture computation here; move integration's header-only shard case. Remove
only now-unused unit fixture/mocking imports, not unrelated tests.

Retain result42 and account/open-empty/closed-object inputs with exact
BacktestError reason and both paths (`strategy.py`/`shard.csv` basenames);
header-only CSV raises `contains no bars` with shard context. Preserve missing
directory `i do not exist` and unused strategy `hello` under disposable state,
asserting FileNotFoundError's offending path. Invalid-result fixtures execute
their actual runners; no patched product validation/computation. Keep all
expected failures independent of implementation.

- **AC-1 DONE** Given retained malformed selected results and empty/missing
  inputs, actual backtests reject with precise contextual errors and unchanged
  input artifacts, without internal doubles or loss of case identities.

  Validation: inspect all four case instances and literal errors; run this
  module, typed unit remainder, ordering legacy case and subtree checks.
