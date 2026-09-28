# Repository Guidelines

## Start Every Task Here

Read [doc/ubiquitous-language.md](doc/ubiquitous-language.md) **in full at the start of every task**, before substantive discussion, planning, defining new terms, review, or implementation. Apply its vocabulary throughout. Reread after context loss or compaction and whenever definitions change. Every agent, including subagents, must do this; include the requirement and relevant vocabulary/contract references when delegating.

When defining, implementing, or reviewing a feat slice, read [doc/feat-workflow.md](doc/feat-workflow.md) **in full before starting that work**.

Then inspect task-relevant code, tests, and ADRs. Distinguish current behavior from intended changes and surface discrepancies affecting the task. Before changing architectural boundaries, read [doc/architecture.md](doc/architecture.md) and follow the [ADR workflow](doc/adr-workflow.md).

## Engineering

Follow [engineering conventions](doc/engineering.md) for code and test changes.

## Repository Map

Ataraxia is a pre-alpha orchestrator for bar-by-bar trading backtests:

- `src/ataraxia/compute/`: computation graph and loop; sibling modules handle sources, providers, features, brokerage, backtesting, and CLI.
- `test/unit/`, `test/integration/`, `test/acceptance/`: tests by boundary.
- `example/`: crossover strategy and its tests; `sample/`: synthetic CSV data.
- `doc/feat/`: feat slices; [doc/adr/](doc/adr/): architectural decisions.

Execution is currently local, sequential, and single-source. Parallel execution, multi-source synchronization, and immutable artifact storage are planned; verify status in code before treating documents as implemented behavior.

## Commands and Validation

Use Python 3.14+, `uv`, and `make`. [Makefile](Makefile) defines executable checks; the [CI workflow](.github/workflows/ci.yml) invokes its shared targets. [CONTRIBUTING.md](CONTRIBUTING.md) covers contribution setup.

| Command | Purpose |
| --- | --- |
| `make setup` | Sync locked dependencies; prepare hook/build environments; install Git hooks |
| `uv sync --locked --group dev` | Verify and install locked dependencies without hooks, as CI does |
| `make lint` / `make format` | Ruff lint with automatic fixes / formatting |
| `make typecheck` | Strict Pyrefly checks on `src/` |
| `make test` | Pytest on `test/` with branch coverage |
| `make verify` | Run all local CI checks offline using prepared dependencies and hooks; excludes the network-dependent audit |
| `make ci` | Verify and sync locked dependencies, audit packages, check YAML/conflict markers/private keys and lint/formatting/types, and run covered tests, examples, and an installed-wheel smoke test |
| `uv run pytest example/` | Example tests, outside default discovery |
| `uv audit --frozen --preview-features audit` | Run the dependency audit alone |
| `uv build` | Build distributions with `uv_build` |

For code changes, run focused tests during development, then `make ci` for all CI checks. When network access is unavailable after setup, run `make verify` for complete local evidence; report the audit separately as unrun or failed. Report checks that could not run. Update and include `uv.lock` when dependencies change.

Run the sample strategy:

```sh
uv run ataraxia --sink example/crossover.py --shards-dir sample --output results.json
```

## Documentation

Follow [documentation ownership](doc/documentation.md) when changing docs or terms.

## Architecture decisions

Follow the [ADR workflow](doc/adr-workflow.md) for architectural decisions.

## Computation and Strategy Contracts

- Keep `compute/` independent of trading concepts and concrete I/O.
- Preserve stable node equality/hashes; equivalent dependencies share computation. Pass the same source instance through dependent nodes. `SourceNode.factory()` returns the runner updated by `send()` (ADR 0012).
- `compute()` owns the source context; the source delegates resource management to its provider (ADR 0016). Explicitly close the generator when stopping consumption early.
- Strategy modules export a sink class as `__sink__`; backtesting constructs it with a source (ADR 0014).
- Rolling windows return newest first. The broker enters at the signal bar's close and evaluates exits on subsequent bars (ADR 0013). Prices/PnL use ticks, four per point for supported instruments. Preserve these conventions unless explicitly changed by the task.

## Contribution

Follow [CONTRIBUTING.md](CONTRIBUTING.md) for commits and pull requests.
