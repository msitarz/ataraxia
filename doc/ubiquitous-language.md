# Ubiquitous language

This file is the single source of truth for Ataraxia's shared vocabulary. Use these
terms consistently in discussions, specifications, code, and tests. Update definitions
as the model evolves; [ADRs](adr/) record the decisions behind architectural changes.
See [architecture.md](architecture.md) for how the concepts fit together.

| Term | Defined in | What it is |
|------|------------|------------|
| `Computable` | [compute/protocol.py](../src/ataraxia/compute/protocol.py) | Protocol for a node in the computable graph |
| `Runner` | [compute/protocol.py](../src/ataraxia/compute/protocol.py) | Callable execution unit for a node |
| `Provider` | [provider.py](../src/ataraxia/provider.py) | Supplies data to a `Source` node (e.g. reads bars from CSV) |
| `Source` | [source.py](../src/ataraxia/source.py) | Computable graph node that passes through whatever the `Provider` fetched onto its dependants |
| `Sink` | [compute/protocol.py](../src/ataraxia/compute/protocol.py) | The terminal node of the graph — what the compute loop resolves to |
| `Bar` | [bar.py](../src/ataraxia/bar.py) | OHLCV data container (currently: CME index futures, 4 ticks/point) |
| `Signal` | [broker.py](../src/ataraxia/broker.py) | Emitted by a strategy (sink node) towards the broker (buy/sell) |
| Shard | [backtest.py](../src/ataraxia/backtest.py) (`backtest_dir`) | One strategy-run's worth of input data, processed independently |
| Feature | [feature.py](../src/ataraxia/feature.py) | Built-in features as computable nodes |
| Broker | [broker.py](../src/ataraxia/broker.py) | Accounts positions and PnL |
