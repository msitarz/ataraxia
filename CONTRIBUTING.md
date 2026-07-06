# Contributing to Ataraxia

## Status

Ataraxia is at pre-alpha, single maintainer, architecture actively in flux. Interfaces, module boundaries, and even the DI/computation model may change without notice. If you're considering non-trivial work, open an issue first; PRs that don't match the current architectural direction won't be merged regardless of code quality.

## Prerequisites

- Python 3.14+
- [`uv`](https://github.com/astral-sh/uv)
- `make`
- Git

## Getting started

```bash
git clone git@github.com:<you>/ataraxia.git
cd ataraxia
make setup
```

`make setup` creates the `uv`-managed virtualenv, installs dependencies (including dev extras), and installs the `prek` pre-commit hooks. Re-run it whenever `pyproject.toml` changes.

## Make targets

| Target           | What it does                                      |
|------------------|---------------------------------------------------|
| `make setup`     | Install deps + prek git hooks hooks               |
| `make lint`      | `ruff check`                                      |
| `make format`    | `ruff format`                                     |
| `make typecheck` | `pyrefly check`                                   |
| `make test`      | `pytest`                                          |
| `make ci`        | lint + typecheck + test — run before opening a PR |
| `make clean`     | remove build artifacts, caches, venv              |

`make ci` is what CI runs. Green locally means green in CI.

## Submitting a change

1. Branch off `main`.
2. `make check` locally before pushing.
3. Open a PR against `main`, referencing the relevant issue if one exists.
4. Wait for review.

## License

Apache 2.0. New source files should carry an SPDX header:

```python
# SPDX-License-Identifier: Apache-2.0
```
