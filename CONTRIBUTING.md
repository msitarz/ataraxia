# Contributing to Ataraxia

## Status

External contributions are gated pending CLA setup via CLA Assistant; none will be
accepted before it is configured. For non-trivial work, create or reuse an issue before
drafting a specification or implementing a change. PRs must match the current
architectural direction. See [project status](README.md#status).

## Prerequisites

- Python satisfying `requires-python` in [pyproject.toml](pyproject.toml)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/), at the exact version required in `pyproject.toml`
- `make`
- Git

## Getting started

```bash
git clone git@github.com:<you>/ataraxia.git
cd ataraxia
make setup
```

`make setup` creates the `uv`-managed virtualenv, installs dependencies (including the
dev group), prepares all pinned hook environments and the wheel build backend, and
installs the `prek` pre-commit and commit-message hooks. Re-run it whenever
`pyproject.toml`, `uv.lock`, or `.pre-commit-config.yaml` changes. Setup needs network
access; caches live in `.cache/uv` and `.cache/prek` by default (override `UV_CACHE_DIR`
or `PREK_HOME` if needed).

The hooks enforce the [commit conventions](#commits-and-pull-requests), with limits: a
body is optional, and neither subject length nor section labels are checked. The body
checker ignores Git comment lines and verbose diffs below the scissors marker, including
Magit commits. Agent-created commits must still follow the additional body requirements
below.

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

After setup, agents without network access can run `make verify`. It checks the locked
environment without installing or resolving dependencies, then reuses the same local
check recipes as CI with uv network access disabled. Missing or stale environments fail;
rerun `make setup` with network access to prepare them. A passing verification does not
include a vulnerability audit; report it separately as unrun or failed when networking
is unavailable. Report checks that could not run.

## Validation selection

Before publishing a draft, run affected local checks and the installed commit
hooks. Select by changed behavior and dependencies, not the file extension alone:

| Change | Local draft checks |
| --- | --- |
| Non-executable prose, navigation or metadata | `git diff --check`; inspect affected document links, anchors, metadata and history until `make docs-check` exists |
| Application code, tests or executable examples | Relevant Ruff, Pyrefly and Tach checks plus focused tests for affected behavior |
| Dependencies, packaging, CI or checker logic | Broader affected checks, including the applicable full suite and setup |

The table sets a minimum; widen checks for cross-file effects or uncertainty.
The proposed docs checker is not implemented yet, so manual document inspection
is reported as manual evidence. A draft PR can open while GitHub CI is pending.
Before merge, require the full CI run on the current review head against the
actual parent. If remote CI cannot run, use `make ci` locally on that head and
report the unavailable remote result; the review remains draft until required
evidence is complete. `make ci` verifies locally before its network audit. An
audit failure fails CI even when its earlier local checks passed.

Reuse an earlier passing result only when its relevant inputs, configuration,
tool versions and environment still match. Record the source revision, command,
outcome and why it remains applicable; never label an unrun command as run on
the current head. A changed dependency invalidates dependent evidence. An audit
has a date and cannot establish current vulnerability status indefinitely.
Pending, failed, reused and unrun checks need distinct reports. CI on the current
review head remains the merge backstop; there is no persistent local cache.

CI rejects a missing or stale `uv.lock` with `uv sync --locked`. Subsequent checks use
the synchronized environment without updating dependency resolution. After intentional
dependency changes, run `uv lock` and commit the updated lockfile. The YAML,
conflict-marker, and private-key checks reuse the pinned hooks in
`.pre-commit-config.yaml` and inspect all tracked files.

For code changes, run focused tests during development, then the complete checks.

Additional commands:

| Command | Purpose |
| --- | --- |
| `uv sync --locked --group dev` | Install locked development dependencies without hooks, as CI does |
| `uv run pytest example/` | Run example tests outside default discovery |
| `uv audit --frozen --preview-features audit` | Run the dependency audit alone |
| `uv build` | Build distributions with the declared build backend |

## Toolchain policy

`pyproject.toml` owns the exact uv pin in `[tool.uv].required-version`. Every CI job
installs that version through `setup-uv`'s `version-file` input; local project commands
reject a different uv version. Install the declared version before running setup (for
example, `uv self update <declared-version>` for a standalone uv installation; use your
package manager for other installations).

The build backend is pinned separately in `[build-system].requires`, because isolated
build requirements are not recorded in `uv.lock`. Keep `uv_build` at the same exact
version as uv so uv builds use its matching bundled backend, while other build frontends
resolve the same backend version.

Review these pins monthly and when a tooling bug or security advisory warrants an
update. Update both pins and the `uv-pre-commit` revision in `.pre-commit-config.yaml`
in one change, install the new uv version, run `uv lock`, and include any lockfile
changes. Run `make ci` before accepting the update, including the installed-wheel smoke
test. Dependabot's weekly uv and GitHub Actions updates complement this review; they do
not replace reviewing the uv executable pin. Python support is declared in
`requires-python`; the [CI workflow](.github/workflows/ci.yml) owns the tested minor
series. OS images and Python patch releases are not pinned by this policy.

`make ci-package` builds a wheel, installs it into a temporary isolated virtual
environment, and runs the copied sample strategy and shards outside the checkout. It
checks the installed console entry point, printed totals, and JSON accounts. The
temporary environment and artifacts are removed when the check finishes.

## Submitting a change

Start feats and unrelated changes from `master` and target their PRs there unless
the task explicitly requires another integration base. Slice and delivery-step
branches/PRs follow the [declared parents and review gates](doc/feat-workflow.md#delivery-branches-and-review-gates).
Use the
[issue template](.github/ISSUE_TEMPLATE/work-item.md) for issue bodies and the
[commit conventions](#commits-and-pull-requests).

For feat slices, read the [feat workflow](doc/feat-workflow.md) in full; it owns branch
naming, issue messages, specification guidance, reviews, and handoffs. For other
documentation work, follow [documentation ownership](doc/documentation.md).

## Commits and pull requests

For small unrelated fixes or documentation edits, use `fix/`, `docs/`, or `chore/`
branches with short lowercase, hyphen-separated names.

Keep commits focused and use Conventional Commits (Commitizen enforced). Use an
imperative subject, aiming for 50 characters including type and scope. Separate the body
with a blank line; hard-wrap prose and bullet continuations at 72 columns, preserving
unbreakable URLs and tokens.

Every agent-created commit must include a succinct body with three labeled sections:
`Why:`, `What:`, and `How:`, separated by blank lines. Explain the problem or
motivation, the resulting change, and the implementation approach, respectively. Keep
each section brief and include relevant validation in `How:`. Avoid repeating the
subject, listing files, or narrating the work session.

PRs explain the problem, resulting behavior, and validation, with relevant issue links.
Follow the [contribution policy](#status) and the base selection above.
