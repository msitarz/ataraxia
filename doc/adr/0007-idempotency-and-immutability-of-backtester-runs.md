# 7. Idempotency and immutability of backtester runs

Date: 2026-07-14

## Status

Accepted

## Context

[6. Massive parallelism via sharding](0006-massive-parallelism-via-sharding.md) transformed the backtesting problem into a data processing pipeline.  This means `ataraxia` will inherit other data pipeline qualities, as well as problems.  One of the problems with distributed processing is double processing.

`Ataraxia` should deal with those problems via good and pragmatic principles.

## Decision

Implement immutability of output artifacts and enable idempotency to mitigate double-processing problem by utilizing standard mechanisms like queues and support for hashing input for each worker to match with output.

Quants will gain immutable output artifiacts for each strategy and shard that they can debug and see how their strategies evolved over time.

## Consequences

`Ataraxia` needs to handle strategy hashing to enable idempotency as well as implement immutability for output artifiacts when processing on cloud platforms.
