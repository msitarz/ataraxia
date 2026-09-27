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

`make setup` creates the `uv`-managed virtualenv, installs dependencies (including the dev group), and installs the `prek` pre-commit and commit-message hooks. Re-run it whenever `pyproject.toml` changes.

Commitizen checks Conventional Commit syntax. The body-formatting hook allows
messages without bodies; when a body is present, separate it from the subject
with a blank line and wrap prose and bullet continuations at 72 columns. Put
unbreakable URLs or tokens on their own lines; indentation, bullet markers, and
trailer labels may precede them. The checker ignores Git comment lines and does
not limit subject length or require section labels. Agent-created commits must
also follow the body structure in [AGENTS.md](AGENTS.md#commits-and-pull-requests).

## Make targets

| Target           | What it does |
|------------------|--------------|
| `make setup`     | Install dependencies and prek Git hooks |
| `make lint`      | Run `ruff check . --fix`; this can modify files |
| `make format`    | Run `ruff format .`; this can modify files |
| `make typecheck` | Run `pyrefly check` |
| `make test`      | Run `pytest --cov` against `test/`, including configured branch coverage |
| `make ci`        | Sync locked dependencies, audit packages, check lint and formatting, type-check, and run covered tests and examples |
| `make clean`     | Remove the virtual environment, Ruff and pytest caches, and `.coverage` |

Before opening a PR, run all CI checks locally:

```sh
make ci
```

## Submitting a change

1. Branch off `master`.
2. Run `make ci` before pushing.
3. Open a PR against `master`, referencing the relevant issue if one exists.
4. Wait for review.

## License

Apache 2.0. New source files should carry an SPDX header:

```python
# SPDX-License-Identifier: Apache-2.0
```
