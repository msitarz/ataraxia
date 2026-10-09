# Complete shipped sample success

After golden delivery, own new `acceptance/test_cli_success.py` and its strict
include. Move only `test_crossover_sample_cli_run` from
`acceptance/test_crossover_sample.py`; leave its failure cases unchanged. Use
merged process/golden helpers and actual shipped example/sample inputs, without
imports of package internals or replacements of product execution.

Preserve exact exit0, empty stderr, complete stdout realized40/unrealized0,
and output.json under tmp_path. Compare the entire parsed artifact against
reviewed golden fields and actual resolved paths; normalize only unspecified
shard order, never omit fields. Preserve input state and case/marker identity.

- **AC-1 TODO** Given shipped example/sample data and prepared tools, the real
  command returns the exact success report and complete independently expected
  artifact at the requested output while retaining inputs unchanged.

  Validation: inspect full comparison/path normalization; run this module and
  legacy failures, plus the CLI subtree's required checks.
