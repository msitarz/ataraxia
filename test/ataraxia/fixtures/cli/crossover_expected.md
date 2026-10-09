# Crossover sample derivation

The fixture records the entry bar when the 12-bar and 26-bar close averages
cross, then the first later bar that reaches a stop or target. Each source
price is converted to ticks by multiplying by four.

- On `nq_15m_2026_07_19.csv`, the averages cross downward at timestamp
  `1784516400` (prior: `65039.3333` / `65039.1923`; current:
  `65028.6667` / `65036.5769`). The close `16239.00` gives entry `64956`;
  the sell target is `64926`. At `1784518200`, the bar reaches that target,
  closing the trade for `+30` ticks.
- The averages cross upward in the same shard at `1784543400` (prior:
  `64490` / `64505.1154`; current: `64509.6667` / `64495.8462`). Close
  `16157.00` gives entry `64628`, stop `64608`, and target `64658`. The
  `1784544300` bar spans both exit levels; the broker's stop-first rule closes
  at `64608` for `-20` ticks.
- On `nq_15m_2026_07_20.csv`, an upward cross at `1784541600` (prior:
  `64308.3333` / `64327.0385`; current: `64327.1667` / `64315.9615`)
  enters at `64450` from close `16112.50`, with target `64480`. The bar at
  `1784542500` reaches the target for `+30` ticks.

The account totals are the sum of closed-trade ticks for each shard; all
positions are closed, so unrealized P&L is zero and the open-position lists are
empty. The JSON preserves the complete entry and closing bars and identifies
the shard and strategy by project-relative path.
