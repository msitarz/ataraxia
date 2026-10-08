# Position outcomes and closing state

After SMA delivery, own new `test/ataraxia/unit/test_position.py` and its strict
include. Move all 13 `test_position*` functions from `test_broker.py`, retaining
their identities as named table rows where appropriate. Use precisely typed
local buy/sell arrangements with explicit Signal fields rather than `asdict`
unpacking. Leave legacy broker fixtures/cases unchanged for their later owner.

Preserve close-price entry 25; long unrealized 3, stop -15/gap -20, target
5/gap 10, both-hit stop priority and persistent closed -15; short target
14/gap 20, stop -4/gap -10 and stored closing PnL -4. Compare complete returned
records plus closing bar/level/PnL. Add both-side equality/neighbor observations
for touched stop/target boundaries; expected values are hand-derived literals.
Broker sequencing, rather than Position alone, owns same-bar-exit prevention.

Do not silently bless a mismatch: `closing_pnl or self.pnl(bar)` in current
production deserves separate scrutiny for a zero-realized closure. Any exposed
contract defect becomes a separate repair, without changing production or
encoding incorrect behavior here.

- **AC-1 DONE** Given the retained long/short lifecycle and price boundaries,
  real Position operations produce complete literal records and persistent
  closing state with stop priority and correctly observed entry/exit levels.

  Validation: review every migrated case and boundary oracle; run the new module
  and unchanged broker remainder, plus the values group's required checks.
