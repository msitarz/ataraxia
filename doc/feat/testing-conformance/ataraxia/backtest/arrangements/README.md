# Valid strategy and loader arrangements

Own `fixtures/backtest/strategy_base.py`, `broker_strategy.py`,
`sink_result_strategy.py`, `import_bar.py`, and `backtest_support.py`, all with
precise normal strict includes. The typed base owns the existing source-driven
Signal runner/Strategy methods; named strategies select broker consumption or
a direct valid sink result. The loader fixture exposes typed `new_bar`.
Own typed copy/path/CSV arrangements and independent result builders here;
copy necessary named modules together without hidden import-path dependence.

Preserve CSV `1,100,200,50,150,1`, buy signal stop100/target200, and loader Bar
whose six fields are all 1. Integer-string prices remain unchanged. Expected
results specify complete account/position fields and resolved paths
independently; do not call backtest or Position processing to generate the
oracle. Leave legacy tests unchanged; consumer adoption follows after merge.

- **AC-1 DONE** Given these retained inputs, named fixture/support artifacts
  expose precise real strategy/loader arrangements and independent expectations
  without generated source or unchecked/forward dependencies.

  Validation: inspect fixture signatures/import/copy dependencies and
  hand-derived results; run strict typing, lint/format, doc/ac checks and legacy
  compatibility cases. Following leaves verify actual loader/graph use, not
  typing alone.
