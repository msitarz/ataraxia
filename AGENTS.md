# Repository Guidelines

## Project Structure & Module Organization

Ataraxia is a pre-alpha orchestrator for immutable, bar-by-bar trading backtests. Python code lives in `src/ataraxia/`: `compute/` implements the computation graph and loop; sibling modules handle sources, providers, features, brokerage, backtesting, and the CLI. Tests are grouped under `test/unit/`, `test/integration/`, and `test/acceptance/`. `example/` contains a crossover strategy and its tests; `sample/` contains synthetic CSV data. Read `doc/architecture.md` and `doc/adr/` before changing architectural boundaries.

## Build, Test, and Development Commands

Use Python 3.14+, `uv`, and `make`.

- `make setup`: synchronize dependencies and install prek pre-commit and commit-message hooks.
- `make lint`: run Ruff with automatic fixes.
- `make format`: format Python files with Ruff.
- `make typecheck`: run strict Pyrefly checks on `src/`.
- `make test`: run pytest with branch coverage.
- `make ci`: check lint, formatting, types, and test coverage before submitting changes.
- `uv run pytest example/test_crossover.py`: run example tests separately, as CI does.
- `uv build`: build distribution artifacts using the configured `uv_build` backend.

Run the sample strategy locally:

```sh
uv run ataraxia --sink example/crossover.py --shards-dir sample --output results.json
```

## Coding Style & Naming Conventions

Use four-space Python indentation, 88-character lines, double quotes, and Google-style docstrings. Follow existing `snake_case` function/module names and `PascalCase` classes. Keep code compatible with strict Pyrefly checking and let Ruff organize imports. Follow `.editorconfig` for UTF-8, LF endings, final newlines, and whitespace. Add `# SPDX-License-Identifier: Apache-2.0` to new source files.

## Testing Guidelines

Use pytest with `test_*.py` files and `test_*` functions. Place tests in the appropriate unit, integration, or acceptance directory, mirroring source modules where practical. Cover changed behavior and relevant edge cases. Coverage must remain at least 80%, with branch measurement enabled. For focused iteration, run `uv run pytest test/unit/test_feature.py`. Default discovery covers `test/`; example tests require a separate invocation.

## Commit & Pull Request Guidelines

Use Conventional Commits, enforced by Commitizen: examples include `test(compute): fix context manager exit method return value` and `docs: update architecture`. Keep changes focused. Describe the problem, resulting behavior, and validation in PRs; link relevant issues. Open an issue before non-trivial architectural work. External contributions are currently gated pending CLA setup; consult `CONTRIBUTING.md` and confirm the target branch, since its branch guidance differs from CI.
