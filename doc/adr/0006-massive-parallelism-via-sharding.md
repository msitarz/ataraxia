# 6. Massive parallelism via sharding

Date: 2026-07-14

## Status

Accepted

## Context

Backtesting involves processing huge amount of data.  Due to the [ADR 5](0005-save-every-computation-step-for-debugging.md), massive amount of data will be produced and stored.

Strategies often involve a specific period of time that they are meant to work in.  Designing the system to support sharding e.g. using a single trading day for intraday strategies can massively boost processing speed and reduce required memory of the entire backtest by using fan-out to workers.

## Decision

Design the system with shard processing in mind, where data is sliced before the processing step and later aggreate the outputs of each processed shard to form the complete backtest stats.

This effectively transform linear backtesting loop into a data pipeline.

## Consequences

Positive:

- Boost performance and reduce overall required memory
- Debug strategies by shard rather than continuous stream of data

Negative:

- Orchestrator complexity will grow substantially
- Need to aggregate results across shards to form complete backtest result
