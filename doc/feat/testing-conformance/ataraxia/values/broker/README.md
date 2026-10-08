# Broker state and account outcomes

After positions delivery, own the remaining five `test_broker_runner*`
functions, `test_sum_accounts`, and local fixtures in
`test/ataraxia/unit/test_broker.py`; add its strict include. Precisely type
arrangements and remove the legacy PositionFixture/asdict plumbing as it is
replaced here, with no dependency on the new position test module or future CLI
result fixtures.

Preserve no-signal, entry, later exit, unrealized update, and signal-while-open
cases. Compare complete account/open/closed snapshots, including Position
entry/closing fields, rather than lengths or selected PnL fields. Snapshot at
each action before later calls mutate live broker collections/accounts; build
independent literal expectations without calling Position to compute them.
Retain account sum 2999/594. Entry must remain open with zero PnL even when its
bar touches an exit; on later calls existing positions update before the new
one is admitted. ADR 13 owns this timing. No broker policy or production repair.

- **AC-1 DONE** Given retained signal/lifecycle cases, the real broker returns
  complete independently expected snapshots, delays new-position exits and
  aggregates account values without internal doubles or mutable-oracle aliasing.

  Validation: inspect snapshots and hand-derived trades against ADR 13/current
  architecture; run broker and position modules, the complete product suite,
  and the values group's required checks, reporting any exposed mismatch.
