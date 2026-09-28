# Contributing to Ataraxia

## Status

Ataraxia is at pre-alpha, single maintainer, architecture actively in flux. Interfaces, module boundaries, and even the DI/computation model may change without notice. If you're considering non-trivial work, create or reuse an issue before drafting the specification or implementing the change; PRs that don't match the current architectural direction won't be merged regardless of code quality.

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
also follow the [body structure below](#commits-and-pull-requests).

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

Before pushing a branch or opening a PR, run all CI checks locally, including for
an early draft PR containing only a specification:

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

For code changes, run focused tests during development, then the complete checks.
Report any checks that could not run. When network access is unavailable after
setup, use local verification and report the audit separately as unrun or failed.

Additional commands:

| Command | Purpose |
| --- | --- |
| `uv sync --locked --group dev` | Install locked development dependencies without hooks, as CI does |
| `uv run pytest example/` | Run example tests outside default discovery |
| `uv audit --frozen --preview-features audit` | Run the dependency audit alone |
| `uv build` | Build distributions with the declared build backend |

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

Branch off `master` and open PRs against `master` unless the task explicitly
requires another base. Use the [issue template](.github/ISSUE_TEMPLATE/work-item.md)
for issue bodies and the general rules in [AGENTS.md](AGENTS.md) for commits.

When defining, implementing, or reviewing a [feat slice](doc/ubiquitous-language.md),
read the [feat slice workflow](doc/feat-workflow.md) in full. It owns branch naming,
issue messages, specification guidance, manual review gates, and session handoffs.
It requires manual specification approval before execution and both manual and
defining-session review of implementation. Keep work in the same PR through
review corrections. The maintainer makes the final merge or close decision.

## License

Apache 2.0. New source files should carry an SPDX header:

```python
# SPDX-License-Identifier: Apache-2.0
```

## Commits and pull requests

For small unrelated fixes or documentation edits, use `fix/`, `docs/`, or `chore/` branches with short lowercase, hyphen-separated names.

Keep commits focused and use Conventional Commits (Commitizen enforced). Use an imperative subject, aiming for 50 characters including type and scope. Separate the body with a blank line; hard-wrap prose and bullet continuations at 72 columns, preserving unbreakable URLs and tokens.

Every agent-created commit must include a succinct body with three labeled sections: `Why:`, `What:`, and `How:`, separated by blank lines. Explain the problem or motivation, the resulting change, and the implementation approach, respectively. Keep each section brief and include relevant validation in `How:`. Avoid repeating the subject, listing files, or narrating the work session.

PRs explain the problem, resulting behavior, and validation, with relevant issue links. External contributions are gated pending CLA setup; follow the [contribution policy](#status). Determine the PR base from explicit task instructions or repository metadata, consistent with contribution guidance.
