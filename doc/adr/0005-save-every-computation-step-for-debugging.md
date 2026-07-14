# 5. Save every computation step for debugging

Date: 2026-07-14

## Status

Accepted

## Context

Strategies are hard to debug as they tend to grow in complexity.  Even as `ataraxia` focuses on testability of features and strategies, debugging actual backtesting results is also very important for the strategy development.

Clear visual debugging need to be enabled by the system.

## Decision

Provide a way to inspect each and every data point that was used by the strategy by introducing an output artifact of each backtest that includes not only strategy results, but also all the inputs to the strategy per each step of the run.

## Consequences

A lot of data will be created per backtester run.
