# 17. Require broker results from backtests

Date: 2026-09-26

## Status

Accepted

## Context

`backtest_shard()` was annotated to return an account, positions, and input paths,
but an integration test used a sink that returned an integer. Changing the return
type to `object` made the annotation match that test while removing the contract
that callers needed. The CLI then had to recover the broker result shape itself.

The computation graph has no trading concepts. Its nodes can return integers or
other values. That does not mean the backtest API needs the same unrestricted
contract. [ADR 14](0014-sink-module-file-special-attribute.md) defines how to load
the strategy; the result also needs a defined shape.

## Decision

Require `backtest_shard()` to return `BacktestShardReturn`: an `Account`, open and
closed `Position` sequences, and absolute strategy and shard paths.
`backtest_dir()` returns a tuple of those records.

Validate the final sink or consumer value at the backtest boundary and construct
the typed record there. Invalid results raise `BacktestResultError` before reaching
callers. The CLI uses the typed result directly. Arbitrary node values remain
supported by the computation graph.

## Consequences

Callers can use the result fields without casts or repeated shape checks. Strategy
modules returning scalar or incomplete results must provide the broker result
fields to run through the backtest API. Tests for generic computation belong with
the compute engine; backtest tests exercise the complete record. Additional
strategy-specific dictionary fields are outside this result contract.
