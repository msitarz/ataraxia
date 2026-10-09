# Named invalid and failing strategy arrangements

After real results, own precisely typed named modules under
`fixtures/backtest/`: `missing_export.py`, `export_none.py`, `export_number.py`,
`export_object.py`, `export_instance.py`, `module_error.py`,
`construction_error.py`, `result_number.py`, `result_non_position.py`; extend
strict includes and only necessary variant-copy selection in
`backtest_support.py`.

Preserve exports absent/None/42/object/Strategy(None), AttributeError("strategy
bug") during module execution or construction, and selected result 42 or account
zero/open empty/closed containing object(). Represent intentionally invalid
values honestly in their own typed fixture contracts, without widening the valid
Strategy or suppressing diagnostics. Reuse merged base definitions only where
semantics remain faithful; copy/import dependencies are explicit.

- **AC-1 DONE** Given the retained invalid inputs, named strict-checked fixtures
  represent every export/error/result variant through real module execution
  without generated edits or broad fallback types.

  Validation: inspect all nine variants, typing and dependency/copy ownership;
  run strict/lint/doc/ac checks and existing compatibility cases. Split this
  fixture delivery before expansion if the complete diff exceeds five minutes.
