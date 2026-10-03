# Ataraxia

Pre-alpha orchestrator for bar-by-bar backtests of trading strategies.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![CI](https://github.com/msitarz/ataraxia/actions/workflows/ci.yml/badge.svg)](https://github.com/msitarz/ataraxia/actions/workflows/ci.yml)

## What it is

Backtests currently run locally and sequentially over CSV shards, using a single
source per backtest. The CLI writes results to a JSON file. Parallel execution
and immutable artifact storage are planned; see the [roadmap](#roadmap).

The workflow idea (work-in-progress) is to prototype strategies visually via
charting software like TradingView, then implement them by composing features
that can be easily unit tested and debugged visually.

## Status

Ataraxia is pre-alpha. Expect breaking changes and shifting design.

## Why was it made

The main ideas:

- Implement features as pure functions that can be composed (feature
  composition) and unit tested.
- Data sharding for parallel processing.
- Bar-by-bar event processing to prevent look-ahead bias.
- Immutable input and output artifacts to avoid running the same backtest twice.

Read [doc/architecture.md](doc/architecture.md) for current behavior and planned
capabilities, and the [ADR index](doc/adr/) for the decisions behind them.

## Development quickstart

Install `uv`. Refer to the
[official documentation](https://docs.astral.sh/uv/getting-started/installation/).

```sh
git clone https://github.com/msitarz/ataraxia
cd ataraxia
make setup
```

Run the example strategy against the sample data:

```sh
make run CLI_ARGS='--sink example/crossover.py --shards-dir sample --output results.json'
```

A sink is a computable graph concept, read more in the
[architecture file](doc/architecture.md).

## Sample data

CSV files in the `sample` folder contain LLM-generated data to showcase a simple
strategy.

## Constraints

Currently there are many constraints in the system which should be removed one
by one in future versions once orchestration is completed. Here is a
non-exhaustive list of such constraints:

- Supports only futures data (4 ticks per point).
- No cost calculation.
- Naive broker with unrealistic fill implementation.
- Processes a single data source.
- Strategy signal supports only market order entry (at current bar close) with
  required TP and SL orders.
- No portfolio tracking, simply returns realized and unrealized PnL.
- PnL accounting per tick, not points or cash.
- Does not support warm-up data (single source limitation).

## Roadmap

### v0.2

- Parallelize locally using concurrent.interpreters

### v0.3

Parallelize via AWS Lambda workers. Fork and deploy on your own AWS account with
private strategies.

- EventBridge fan-out to Lambda workers that process a single shard and a
  strategy
- S3 immutable artifacts (strategies, shards, output)
- Strategy check via CLI (like ruff check) to prevent invalid strategy
  deployment

### Future versions

- Output artifact schema with all computation steps.
- SQLite (for local runs) and AWS DSQL for artifact indexing and aggregation
  across backtest runs.
- Web-based UI to view backtest runs with charts to debug strategies with exact
  features and strategies' inputs and outputs for each computation step.
- Implementation of common features.
- Multi-source processing.
- Live data feed processing to transform ataraxia into an electronic trading
  assistant.

## License

Apache License 2.0. See [LICENSE](LICENSE). SPDX headers are present on source
files.

This repository is not yet open to external contributions — a CLA (via CLA
Assistant) will be configured before the first external PR is accepted.
