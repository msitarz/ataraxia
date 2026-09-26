# Repository Guidelines

## Project Structure & Module Organization

Ataraxia is a pre-alpha orchestrator for bar-by-bar trading backtests. Python code lives in `src/ataraxia/`: `compute/` implements the computation graph and loop; sibling modules handle sources, providers, features, brokerage, backtesting, and the CLI. Tests are grouped under `test/unit/`, `test/integration/`, and `test/acceptance/`. `example/` contains a crossover strategy and its tests; `sample/` contains synthetic CSV data. Read `doc/architecture.md` and relevant records in `doc/adr/` before changing architectural boundaries.

Current execution is local, sequential, and single-source. Parallel execution, multi-source synchronization, and immutable artifact storage are planned. Verify implementation status in code before treating architecture or feature documents as existing behavior.

## Build, Test, and Development Commands

Use Python 3.14+, `uv`, and `make`.

- `make setup`: synchronize dependencies and install prek pre-commit and commit-message hooks.
- `uv sync --frozen --group dev`: install locked dependencies without installing Git hooks, as CI does.
- `make lint`: run Ruff with automatic fixes.
- `make format`: format Python files with Ruff.
- `make typecheck`: run strict Pyrefly checks on `src/`.
- `make test`: run pytest with branch coverage.
- `make ci`: check lint, formatting, types, and test coverage before submitting changes.
- `uv run pytest example/`: run example tests separately from default test discovery.
- `uv audit --frozen --preview-features audit`: audit dependencies, as CI does separately from `make ci`.
- `uv build`: build distribution artifacts using the configured `uv_build` backend.

When changing dependencies, update and include `uv.lock`. Use the Makefile and CI workflow to verify executable commands; `CONTRIBUTING.md` currently references a nonexistent `make check` target.

Run the sample strategy locally:

```sh
uv run ataraxia --sink example/crossover.py --shards-dir sample --output results.json
```

## Computation and Strategy Contracts

- Keep `compute/` independent of trading concepts and concrete I/O implementations.
- Preserve stable node equality and hashes throughout execution; equivalent dependency specifications share computation. Pass the same source instance through dependent nodes. `SourceNode.factory()` must return the runner updated by `send()` (ADR 0012).
- `compute()` owns the source context; the source delegates resource management to its provider (ADR 0016). Callers that stop consuming the compute generator early should explicitly close it.
- Strategy modules export a sink class through `__sink__`; backtesting constructs it with a source instance (ADR 0014).
- Rolling windows return newest values first. The current broker enters positions at the signal bar's close and begins evaluating their exits on subsequent bars (ADR 0013). Prices and PnL use ticks, with four ticks per point for supported instruments. Preserve these conventions unless the task explicitly changes them.

## Code style

Use four-space Python indentation, 88-character lines, double quotes, and Google-style docstrings. Follow existing `snake_case` function/module names and `PascalCase` classes. Keep code compatible with strict Pyrefly checking and let Ruff organize imports. Follow `.editorconfig` for UTF-8, LF endings, final newlines, and whitespace. Add `# SPDX-License-Identifier: Apache-2.0` to new source files.

- Prefer function composition over nested control flow. Keep functions and methods focused, and use guard clauses and early returns to keep nesting shallow. Treat roughly 25 lines of executable code as a review signal; extract helpers when they represent a cohesive operation or improve readability.
- Inject dependencies through function arguments or constructor/dataclass fields instead of monkey patching globals or collaborators. Use the same injection points in tests with small fakes or stubs implementing the required behavior. Only when injection is impractical and patching is absolutely necessary, use `unittest.mock.patch` in a scoped context manager instead of pytest's `monkeypatch` fixture.
- Define collaborator interfaces with `typing.Protocol` and structural duck typing; callers should depend on the required protocol rather than a concrete implementation. Value objects and internal helpers do not all need protocols. Use `@runtime_checkable` when runtime protocol checks are needed, following `src/ataraxia/compute/protocol.py` and `src/ataraxia/provider.py`.
- Describe structured data with dataclasses. Prefer `@dataclass(frozen=True)` for value objects and computable node specifications, and use `field(default_factory=...)` for per-instance containers or collaborators. Keep node specifications hashable; put execution state in their callable runners, following `src/ataraxia/source.py` and `src/ataraxia/feature.py`.
- Avoid raw dictionaries for records with known fields. Prefer dataclasses, or `TypedDict` when a dictionary representation is required, as in `BrokerReturn` and `BacktestShardReturn`. Reserve general mappings for truly dynamic keys, such as computable graph nodes or dependency names. Prefer `TypedDict` wherever the key schema can be described; for genuinely arbitrary keys, use explicitly typed `Mapping[K, V]` or `MutableMapping[K, V]` contracts.
- Translate expected low-level failures at library boundaries into contextual domain exceptions defined in `src/ataraxia/errors.py`. Derive new domain exceptions from `AtaraxiaError`, retain a relevant built-in exception base where appropriate, and preserve the cause with `raise DomainError("Useful context") from exc`, following `sort_graph` in `src/ataraxia/compute/graph.py`. Avoid blanket wrapping of programming errors or normal iteration termination. Document domain errors callers are expected to handle in a Google-style `Raises` section.
- Follow the computation node pattern: `deps()` declares named inputs, `factory()` supplies a runner, and the runner's `__call__` performs computation. Match dependency keys to runner parameter names. Extract reusable calculations into standalone functions, as `SmaRunner` does with `sma`.
- Use modern Python typing: `T | None`, built-in generics, `type` aliases, and parameterized protocols/classes. Prefer `collections.abc` interfaces such as `Sequence`, `Mapping`, and `Iterator` in contracts; require mutable interfaces only when mutation is needed. Use `Literal` for closed sets of values, as with signal sides.
- Use context managers for files and providers so resources close on success and failure. Follow the source/provider context-manager delegation pattern, and use `pathlib.Path` for filesystem paths.
- Keep console output in `src/ataraxia/cli.py`; library functions return values or raise domain errors. Use pytest fixtures for reusable test inputs, `pytest.raises` for error behavior, `tmp_path` for filesystem tests, and `capsys` for CLI output assertions.

## Testing Guidelines

Use pytest with `test_*.py` files and `test_*` functions. Place tests in the appropriate unit, integration, or acceptance directory, mirroring source modules where practical. Cover changed behavior and relevant edge cases. Coverage must remain at least 80%, with branch measurement enabled. For focused iteration, run `uv run pytest test/unit/test_feature.py`. Default discovery covers `test/`; example tests require a separate invocation.

For relevant changes, cover dependency sharing and runner state, provider cleanup on exhaustion/error/explicit generator closure, rolling-window ordering and warm-up behavior, and broker timing that prevents same-bar exits for newly opened positions. Use integration tests for real strategy loading and acceptance tests for CLI output and artifacts.

For code changes, run focused tests during development, then `make ci` and `uv run pytest example/`. CI additionally performs frozen dependency synchronization and package auditing. Report checks that could not run.

## Commit & Pull Request Guidelines

Use Conventional Commits, enforced by Commitizen: examples include `test(compute): fix context manager exit method return value` and `docs: update architecture`. Keep changes focused. Describe the problem, resulting behavior, and validation in PRs; link relevant issues. Open an issue before non-trivial architectural work. Record architectural changes in an ADR and update `doc/architecture.md`.

External contributions are currently gated pending CLA setup. Before opening a PR, determine the intended base from repository metadata or explicit task instructions; ask only if it remains ambiguous. `CONTRIBUTING.md` names `main`, while CI's push trigger names `master`; the trigger alone does not establish the intended PR base.
