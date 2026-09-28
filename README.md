# Ataraxia

Pre-alpha orchestrator for bar-by-bar backtests of trading strategies.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![CI](https://github.com/msitarz/ataraxia/actions/workflows/ci.yml/badge.svg)](https://github.com/msitarz/ataraxia/actions/workflows/ci.yml)

## What it is

Run trading strategies against CSV shards and inspect JSON results.
See [architecture](doc/architecture.md) for implemented capabilities and the
[roadmap](#roadmap) for priorities.

The workflow idea (work-in-progress) is to prototype strategies visually via charting software like TradingView, then implement them by composing features that can be easily unit tested and debugged visually.

## Status

Ataraxia is pre-alpha, maintained by a single maintainer. Expect breaking changes
and shifting design.

## Why was it made

The main ideas:
- Implement features as pure functions that can be composed (feature composition) and unit tested.
- Data sharding for parallel processing.
- Bar-by-bar event processing to prevent look-ahead bias.
- Immutable input and output artifacts to avoid running the same backtest twice.

Read [doc/architecture.md](doc/architecture.md) for current behavior and planned
capabilities, and the [ADR log](doc/adr/) for the decisions behind them.

## Quickstart

Follow [development setup](CONTRIBUTING.md#getting-started), then run the
example strategy against the sample data:

```sh
uv run ataraxia --sink example/crossover.py --shards-dir sample --output results.json
```

See the [glossary](doc/ubiquitous-language.md) for shared terms and
[architecture](doc/architecture.md) for current behavior and limitations.

## Sample data

CSV files in the `sample` folder contain LLM-generated data to showcase a simple strategy.

## Roadmap

### v0.2

- Local parallel execution implemented on the feat branch; see the
  [feat slice](doc/feat/parallel-execution.md).

### v0.3

Cloud execution and immutable artifacts; see the
[planned deployment model](doc/architecture.md#target-execution-and-deployment).
Also planned: strategy validation via CLI before deployment.

### Future versions

- Output artifact schema with all computation steps.
- SQLite (for local runs) and AWS DSQL for artifact indexing and aggregation across backtest runs.
- Web-based UI to view backtest runs with charts to debug strategies with exact features and strategies' inputs and outputs for each computation step.
- Implementation of common features.
- Multi-source processing.
- Live data feed processing to transform ataraxia into an electronic trading assistant.

## License

Apache License 2.0. See [LICENSE](LICENSE) and
[contribution policy](CONTRIBUTING.md#status).
