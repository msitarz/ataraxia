# Real shard, directory and selected results

After loading, own new `integration/test_backtest_results.py` and its strict
include. Move `test_backtest_shard` and `test_backtest_dir` from integration's
legacy module and replace unit's
`test_backtest_shard_include_shard_path_strategy_path` with real execution here.
Adopt merged arrangements; leave all other legacy cases untouched. Avoid
adopting their unclean fixtures/helpers by implication.

Assert complete independent accounts, open/closed Positions and exact resolved
strategy/shard paths. Preserve the one-bar open buy position at entry150, zero
account PnL, and first_shard/second_shard inputs without assuming directory
iteration order. The migrated path case retains `somefile.py`/`somedir`
basenames as real disposable strategy/CSV files. Add real direct-sink and
broker-consumer cases under ADR 14; do not patch
compute/import_file/is_sink/is_type. These show natural selected results, not
mapping-order independence, which has its separate leaf.

- **AC-1 TODO** Given retained real strategy/shard arrangements, shard and
  directory backtests return complete literal enriched results and choose the
  real sink/consumer outcome without replacing product computation.

  Validation: compare migrated case identities and hand-derived complete
  expectations; run this module, both legacy remainders and subtree checks.
