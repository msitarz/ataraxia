# Ubiquitous language

This file is the single source of truth for Ataraxia's shared vocabulary. Use these
terms consistently in discussions, specifications, code, and tests. Update definitions
as the model evolves; [ADRs](adr/) record the decisions behind architectural changes.
See [architecture.md](architecture.md) for how the concepts fit together.

| Term | Defined in | What it is |
|------|------------|------------|
| `Computable` | [compute/protocol.py](../src/ataraxia/compute/protocol.py) | A hashable graph-node specification. It declares named dependencies and supplies the runner that executes it; execution state belongs to that runner. |
| `Runner` | [compute/protocol.py](../src/ataraxia/compute/protocol.py) | The callable execution instance supplied by `Computable.factory()`. It receives dependency values at each step and may retain execution state. `SourceNode` retains its runner so `send()` and graph execution use the same instance. |
| `Provider` | [provider.py](../src/ataraxia/provider.py) | A hashable, context-managed iterator that supplies input items; for example, `BarProvider` reads bars from a CSV shard. `SourceNode` adapts a provider into the computation graph. |
| `Source` | [compute/protocol.py](../src/ataraxia/compute/protocol.py), [source.py](../src/ataraxia/source.py) | An iterable, context-managed `Computable` input node. The loop passes each yielded item to `send()` before evaluating the graph. `SourceNode` delegates iteration and resource management to its provider. Current `compute()` supports exactly one source. |
| `Sink` | [compute/protocol.py](../src/ataraxia/compute/protocol.py), [loop.py](../src/ataraxia/compute/loop.py) | The graph's primary endpoint. It declares its sources and may name an optional downstream `consumer`; the loop evaluates `consumer() or sink`, and the backtest returns that selected node's last result. |
| `consumer` | [compute/protocol.py](../src/ataraxia/compute/protocol.py), [broker.py](../src/ataraxia/broker.py) | An optional downstream `Computable` returned by a `Sink`. It receives the sink's value to aggregate it or perform final computation; `Broker` is the current example. |
| Strategy | [backtest.py](../src/ataraxia/backtest.py), [ADR 14](adr/0014-sink-module-file-special-attribute.md) | A caller-defined `Sink` whose runner derives values or `Signal`s from source data and features. A backtest module exports its sink class as `__sink__`, and backtesting constructs it with the source. |
| Feature | [feature.py](../src/ataraxia/feature.py), [ADR 3](adr/0003-feature-composition.md) | A composable `Computable` that derives a value from source data or other features. Features may be supplied by Ataraxia or defined with a strategy. |
| Shard | [backtest.py](../src/ataraxia/backtest.py), [ADR 6](adr/0006-massive-parallelism-via-sharding.md) | An input-data partition processed independently for a strategy. Current backtesting reads bars from a CSV file for each shard, processes shards sequentially, and returns per-shard results. The CLI aggregates their account totals. |
| `Bar` | [bar.py](../src/ataraxia/bar.py) | An OHLCV input value. Current normalization supports CME index futures with four ticks per point. |
| `Signal` | [broker.py](../src/ataraxia/broker.py) | A strategy output that asks a broker to open a buy or sell market position with stop-loss and take-profit levels. |
| Position | [broker.py](../src/ataraxia/broker.py) | A broker record created from a `Signal` and its entry `Bar`; it tracks entry, exit, and realized or unrealized PnL. The current broker enters at the signal bar's close and evaluates exits from later bars. |
| Account | [broker.py](../src/ataraxia/broker.py) | The broker's current total realized PnL and unrealized PnL across its positions. |
| Broker | [broker.py](../src/ataraxia/broker.py) | A downstream `consumer` computable that turns `Signal`s and bars into an `Account`, open positions, and closed positions. |
