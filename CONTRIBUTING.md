# Contributing to Ataraxia

## Status

Ataraxia is at pre-alpha, single maintainer, architecture actively in flux. Interfaces, module boundaries, and even the DI/computation model may change without notice. If you're considering non-trivial work, open an issue first; PRs that don't match the current architectural direction won't be merged regardless of code quality.

## Prerequisites

- Python 3.14+
- [`uv`](https://github.com/astral-sh/uv), at the exact version required in `pyproject.toml`
- `make`
- Git

## Getting started

```bash
git clone git@github.com:<you>/ataraxia.git
cd ataraxia
make setup
```

`make setup` creates the `uv`-managed virtualenv, installs dependencies (including the dev group), prepares all pinned hook environments and the wheel build backend, and installs the `prek` pre-commit and commit-message hooks. Re-run it whenever `pyproject.toml`, `uv.lock`, or `.pre-commit-config.yaml` changes. Setup needs network access; caches live in `.cache/uv` and `.cache/prek` by default (override `UV_CACHE_DIR` or `PREK_HOME` if needed).

Commitizen checks Conventional Commit syntax. The body-formatting hook allows
messages without bodies; when a body is present, separate it from the subject
with a blank line and wrap prose and bullet continuations at 72 columns. Put
unbreakable URLs or tokens on their own lines; indentation, bullet markers, and
trailer labels may precede them. The checker ignores Git comment lines and the
verbose diff below Git's scissors marker (including Magit commits). It does
not limit subject length or require section labels. Agent-created commits must
also follow the body structure in [AGENTS.md](AGENTS.md#commits-and-pull-requests).

## Make targets

| Target           | What it does |
|------------------|--------------|
| `make setup`     | Sync locked dependencies, prepare hook/build environments, and install Git hooks |
| `make verify`    | Verify the prepared environment and run every local CI check offline, including examples and the installed-wheel smoke test |
| `make lint`      | Run `ruff check . --fix`; this can modify files |
| `make format`    | Run `ruff format .`; this can modify files |
| `make typecheck` | Run strict Pyrefly and positive/negative type expectations |
| `make arch-check` | Run Tach internal and external dependency checks |
| `make test`      | Run `pytest --cov` against `test/`, including configured branch coverage |
| `make ci`        | Verify and sync locked dependencies, audit packages, check YAML/conflict markers/private keys, check lint and formatting, type-check, check architecture, and run covered tests, examples, and an installed-wheel smoke test |
| `make clean`     | Remove the virtual environment, Ruff and pytest caches, and `.coverage` |

After setup, agents without network access can run `make verify`. It checks the
locked environment without installing or resolving dependencies, then reuses the
same local check recipes as CI with uv network access disabled. Missing or stale
environments fail; rerun `make setup` with network access to prepare them. A passing
verification does not include a vulnerability audit.

Before opening a PR, run all CI checks locally:

```sh
make ci
```

Full `make ci` runs local verification before the required network-dependent audit.
An audit failure still fails CI, while completed local results remain available.
The CI check job also runs its local checks before auditing.

CI rejects a missing or stale `uv.lock` with `uv sync --locked`. Subsequent checks
use the synchronized environment without updating dependency resolution. After
intentional dependency changes, run `uv lock` and commit the updated lockfile.
The YAML, conflict-marker, and private-key checks reuse the pinned hooks in
`.pre-commit-config.yaml` and inspect all tracked files.

## Toolchain policy

`pyproject.toml` owns the exact uv pin in `[tool.uv].required-version`.
Every CI job installs that version through `setup-uv`'s `version-file` input;
local project commands reject a different uv version. Install the declared
version before running setup (for example, `uv self update 0.12.19` for a
standalone uv installation; use your package manager for other installations).

The build backend is pinned separately in `[build-system].requires`, because
isolated build requirements are not recorded in `uv.lock`. Keep `uv_build` at
the same exact version as uv so uv builds use its matching bundled backend,
while other build frontends resolve the same backend version.

Review these pins monthly and when a tooling bug or security advisory warrants
an update. Update both pins and the `uv-pre-commit` revision in
`.pre-commit-config.yaml` in one change, install the new uv version, run
`uv lock`, and include any lockfile changes. Run `make ci` before accepting the
update, including the installed-wheel smoke test. Dependabot's weekly uv and
GitHub Actions updates complement this review; they do not replace reviewing
the uv executable pin. Python remains supported at 3.14+; CI tests the 3.14
minor series. OS images and Python patch releases are not pinned by this policy.

`make ci-package` builds a wheel, installs it into a temporary isolated virtual
environment, and runs the copied sample strategy and shards outside the checkout.
It checks the installed console entry point, printed totals, and JSON accounts.
The temporary environment and artifacts are removed when the check finishes.

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
