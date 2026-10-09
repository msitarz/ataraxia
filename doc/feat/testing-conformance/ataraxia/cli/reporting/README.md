# Complete display and serialization units

After arrangements, own new `unit/test_cli_reporting.py` and its strict include.
Move only `test_display_results`, `test_save_results` and adopted fixture use
from `unit/test_cli.py`; remove its unused broker_returns plumbing. Leave its
patched main case untouched until the failure-flow replacement delivers.

Exercise real display_results/save_results. Assert complete stdout with realized
80/unrealized -40 and empty stderr, and complete parsed saved JSON matching the
merged independent artifact, including all position fields/nulls. Preserve
`out.json` under tmp_path. Precisely annotate fixture parameters and captures
with supported public pytest types; avoid production computation in the oracle.

- **AC-1 TODO** Given retained typed broker inputs, real public display/save
  produce the exact report and complete independent serialized values without
  changing input data or writing outside disposable output.

  Validation: review migrated identities/full expectations; run this module and
  the legacy main remainder, plus the CLI subtree's required checks.
