# Contributing to Ataraxia

## Status

Ataraxia is pre-alpha, has a single maintainer, and its architecture is actively
in flux. Interfaces, module boundaries, and the DI/computation model may change
without notice. PRs that don't match the current architectural direction won't
be merged regardless of code quality.

Works use their local contracts and PRs without routine issues. Use the
[issue template](.github/ISSUE_TEMPLATE/work-item.md) for bugs and
collaboration.

## Prerequisites

- Python 3.14+
- [`uv`](https://github.com/astral-sh/uv), at the exact version required in
  `pyproject.toml`
- `make`
- Git

## Getting started

```bash
git clone git@github.com:<you>/ataraxia.git
cd ataraxia
make setup
```

`make setup` creates the `uv`-managed virtualenv, installs dependencies
(including the dev group), prepares all pinned hook environments and the wheel
build backend, and installs the `prek` pre-commit and commit-message hooks.
Re-run it whenever `pyproject.toml`, `uv.lock`, or `.pre-commit-config.yaml`
changes. Setup needs network access; caches live in `.cache/uv` and
`.cache/prek` by default (override `UV_CACHE_DIR` or `PREK_HOME` if needed).

Commitizen checks Conventional Commit syntax. The body-formatting hook allows
messages without bodies; when a body is present, separate it from the subject
with a blank line and wrap prose and bullet continuations at 72 columns. Put
unbreakable URLs or tokens on their own lines; indentation, bullet markers, and
trailer labels may precede them. The checker ignores Git comment lines and the
verbose diff below Git's scissors marker (including Magit commits). It does
not limit subject length or require section labels. Agent-created commits must
also follow the [body structure below](#commits-and-pull-requests).

## Make targets

Humans and agents should run `make help` before project tools to find supported
targets. The [Makefile](Makefile) owns executable commands and descriptions;
read recipes only when their details matter. See the
[validation policy](doc/validation.md) when choosing checks or reporting
validation evidence.

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
`uv lock`, and include any lockfile changes. Follow the
[validation policy](doc/validation.md) before accepting the update, including
the installed-wheel smoke test. Dependabot's weekly uv and GitHub Actions
updates complement this review; they do not replace reviewing
the uv executable pin. Python remains supported at 3.14+; CI tests the 3.14
minor series. OS images and Python patch releases are not pinned by this policy.

## Submitting a change

For changes outside a Work, branch off `master` and target PRs to `master`
unless the task explicitly requires another base. Use the
[issue template](.github/ISSUE_TEMPLATE/work-item.md) for issue bodies and the
[commit conventions](#commits-and-pull-requests).

### Running Git commands

Run each Git operation in a separate tool call; do not chain Git commands with
shell operators. If an operation requiring escalation is denied, canceled, or
fails, stop and report the exact command and result immediately. Do not retry
silently or manipulate Git lock files.

### Work branches, review, and merge

Start each Work branch from current `master` and target its PR to `master`. Only
an explicit maintainer instruction permits another base and PR target, such as
for a Prototype or rewrite; identify the exception in the PR.

Follow the [Work scope and sizing rules](doc/workflow.md#scope-and-sizing) for
reviewable deliveries. Material changes to an approved direction or contract
require explicit approval; smaller Works within that direction proceed to their
own review. The maintainer reviews the current PR revision and performs the
merge. Agents must not merge without an explicit instruction.

PRs carry review discussion and rationale. Use the commit subject and concise
PR description conventions below. Merged PRs and recorded approvals provide
durable decisions across sessions. Remove merged remote and local branches when
no dependent PR needs them. Retained branches and GitHub status queries are not
routine Work tracking; use the [Work lifecycle](doc/workflow.md) for parent
status rules.

## Commits and pull requests

For small unrelated fixes or documentation edits, use `fix/`, `docs/`, or
`chore/` branches with short lowercase, hyphen-separated names.

Keep commits focused and use Conventional Commits (Commitizen enforced). Use an
imperative subject, aiming for 50 characters including type and scope. Separate
the body with a blank line; hard-wrap prose and bullet continuations at 72
columns, preserving unbreakable URLs and tokens.

PRs explain the problem and resulting behavior. External contributions are gated
pending CLA setup (see [Status](#status)). Determine the PR base from explicit
task instructions or repository metadata, consistent with the guidance above.

## License

Apache 2.0. New source files should carry an SPDX header:

```python
# SPDX-License-Identifier: Apache-2.0
```
