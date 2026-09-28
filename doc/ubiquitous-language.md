# Ubiquitous language

This file owns shared meanings and distinctions. Use these terms in discussion,
specifications, code, and tests. Sections separate responsibilities; a term can
relate to another section without sharing its meaning. Planned terms identify
proposals, not implemented capabilities.

[Architecture](architecture.md) explains current relationships;
[ADRs](adr/) preserve architectural rationale. Local contracts and defaults live
in the linked feat slices. Follow [documentation ownership](documentation.md#vocabulary)
when adding or changing terms.

## Computation

| Term | References | Meaning |
| --- | --- | --- |
| `Computable` | [compute/protocol.py](../src/ataraxia/compute/protocol.py) | A hashable graph-node specification. It declares named dependencies and supplies the runner that executes it; execution state belongs to that runner. |
| `Runner` | [compute/protocol.py](../src/ataraxia/compute/protocol.py) | The callable execution instance supplied by `Computable.factory()`. It receives dependency values at each step and may retain execution state. |
| `Provider` | [provider.py](../src/ataraxia/provider.py) | A hashable, context-managed iterator that supplies input items; for example, `BarProvider` reads bars from a CSV shard. `SourceNode` adapts a provider into the computation graph. |
| `Source` | [compute/protocol.py](../src/ataraxia/compute/protocol.py), [source.py](../src/ataraxia/source.py) | An iterable, context-managed `Computable` input node. It supplies items to the graph through its runner; `SourceNode` adapts a provider. |
| `Sink` | [compute/protocol.py](../src/ataraxia/compute/protocol.py), [loop.py](../src/ataraxia/compute/loop.py) | The graph's primary endpoint. It declares its sources and may select an optional downstream `consumer`. |
| `consumer` | [compute/protocol.py](../src/ataraxia/compute/protocol.py), [broker.py](../src/ataraxia/broker.py) | An optional downstream `Computable` selected by a `Sink` to aggregate its values or perform final computation; `Broker` is the current example. |

## Trading and backtesting

| Term | References | Meaning |
| --- | --- | --- |
| Strategy | [backtest.py](../src/ataraxia/backtest.py), [ADR 14](adr/0014-sink-module-file-special-attribute.md) | A caller-defined `Sink` whose runner derives values or `Signal`s from source data and features. |
| Feature | [feature.py](../src/ataraxia/feature.py), [ADR 3](adr/0003-feature-composition.md) | A composable `Computable` that derives a value from source data or other features. Features may be supplied by Ataraxia or defined with a strategy. |
| Shard | [backtest.py](../src/ataraxia/backtest.py), [ADR 6](adr/0006-massive-parallelism-via-sharding.md) | An input-data partition processed independently for a strategy, with results aggregated across partitions. |
| `Bar` | [bar.py](../src/ataraxia/bar.py) | An OHLCV input value. Current normalization supports CME index futures with four ticks per point. |
| `Signal` | [broker.py](../src/ataraxia/broker.py) | A strategy output that asks a broker to open a buy or sell market position with stop-loss and take-profit levels. |
| Position | [broker.py](../src/ataraxia/broker.py) | A broker record created from a `Signal` and its entry `Bar`, tracking entry, exit, and realized or unrealized PnL. |
| Account | [broker.py](../src/ataraxia/broker.py) | The broker's current total realized PnL and unrealized PnL across its positions. |
| Broker | [broker.py](../src/ataraxia/broker.py) | A downstream `consumer` computable that turns `Signal`s and bars into an `Account`, open positions, and closed positions. |

## Orchestration and execution

| Term | References | Meaning |
| --- | --- | --- |
| Shard input | [Parallel execution feat slice](feat/parallel-execution.md) | A planned execution request identifying a strategy and shard. It carries input references, not live computation objects or execution state. |
| Shard outcome | [Parallel execution feat slice](feat/parallel-execution.md) | A planned record identifying a strategy and shard, containing either a successful result or a failure diagnostic. |
| Shard error | [Parallel execution feat slice](feat/parallel-execution.md) | A planned serializable diagnostic for a shard execution exception, timeout, or executor worker failure. |
| Orchestrator | [Architecture](architecture.md), [ADR 18](adr/0018-supervise-process-workers-for-shard-timeouts.md) | The backtest application responsibility that discovers independent shards, dispatches shard inputs, and collects shard outcomes. Worker supervision is planned in ADR 18. |
| Executor worker | [ADR 18](adr/0018-supervise-process-workers-for-shard-timeouts.md) | A planned child process executing shard inputs and returning shard outcomes. It is distinct from a graph runner; assignments construct fresh runners. |
| Process pool | [ADR 18](adr/0018-supervise-process-workers-for-shard-timeouts.md) | A planned bounded set of executor workers owned by the orchestrator. This does not imply Python's `ProcessPoolExecutor`. |
| Shard timeout | [Parallel execution feat slice](feat/parallel-execution.md) | A planned wall-clock deadline for a shard assignment, measured in seconds. Its timing and expiry contract belong to the parallel execution slice. |

## Delivery workflow

| Term | References | Meaning |
| --- | --- | --- |
| Feat slice | [Feat workflow](feat-workflow.md), [doc/feat/](feat/) | A small delivery increment with a specification in `doc/feat/`, defining an observable outcome, scope, acceptance examples, and validation evidence. It may deliver an accepted specification or implemented behavior. It is distinct from a trading Feature. |
| Defining session | [Feat workflow](feat-workflow.md#roles-and-handoffs) | The agent session responsible for defining a feat slice and reviewing its implementation against the approved specification. This is a delivery role, not a graph runner or executor worker. |
| Executor session | [Feat workflow](feat-workflow.md#roles-and-handoffs) | The agent session responsible for implementing an approved feat slice, recording validation evidence, and addressing review findings. This is a delivery role, not a graph runner or executor worker. |
