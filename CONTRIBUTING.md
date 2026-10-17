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
- [`uv`](https://github.com/astral-sh/uv) satisfying the version requirement in
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

To create an agent [worktree](doc/ubiquitous-language.md) from local `master`,
run `make worktree-create WORKTREE=/path/to/worktree BRANCH=work/example`. The
target copies `.cache` when present, creates a fresh `.venv` with offline
`ci-setup`, and runs `verify-setup` before reporting readiness. If setup fails,
the worktree remains available for recovery; follow the printed instructions
from inside that worktree.

Commitizen checks Conventional Commit syntax. The body-formatting hook allows
messages without bodies; when a body is present, separate it from the subject
with a blank line and wrap prose and bullet continuations at 72 columns. Put
unbreakable URLs or tokens on their own lines; indentation, bullet markers, and
trailer labels may precede them. The checker ignores Git comment lines and the
verbose diff below Git's scissors marker (including Magit commits). It does
not limit subject length or require section labels. Agent-created commits
follow the same [commit conventions](#commits-and-pull-requests).

## Make targets

Invoke project tools through Make targets. Consult `make help` when a target is
unfamiliar, current target knowledge is missing, or the Make interface may have
changed. Reuse known current targets across turns; recheck when uncertain or
after an interface change. This discovery step does not apply to Git or GitHub
commands. Do not prefix Make calls with environment-variable assignments;
targets own their required runtime environment. Use documented Make command-line
inputs, such as `make test ARGS=test/make/integration`, instead of an ad hoc
environment wrapper. Use space-separated repo paths in `ARGS` to narrow lint,
format, test, and type-check runs; full-suite targets keep their full defaults.
If a required project invocation is not exposed, add or extend a Make target
instead of bypassing Make. The [Makefile](Makefile) owns executable commands and
descriptions; read recipes only when their details matter. See the
[check and evidence policy](doc/validation.md) when choosing checks or reporting
evidence.

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

Start the maintainer's requested Work branch from current `master` and target
its final PR to `master`. Within that requested tree, the orchestrator assigns
isolated child-parent branches/worktrees and base refs under
[orchestrator guidance](doc/orchestrator.md#roles-and-delegation). Executors
follow [executor guidance](doc/executor.md) to verify the supplied assignment
before editing.
Direct leaves accumulate locally and do not open separate PRs. Only an explicit
maintainer instruction permits another requested-Work base or PR target;
identify the exception in the PR.

Follow the [Work scope and sizing rules](doc/workflow.md#scope-and-sizing) for
reviewable deliveries. Material changes to an approved direction or contract
require explicit approval; smaller Works within that direction proceed to their
own review.

For Work PRs with acceptance criteria, keep requested and descendant contracts
through review, corrections, and maintainer merge. Follow
[Work acceptance](doc/acceptance-tracing.md#work-delivery) for observed
evidence and correction updates. Do not remove contracts in a pre-publication
cleanup commit.

Before preparing a published-branch rewrite, follow
[publisher rewrite guidance](doc/publisher.md#published-branch-rewrites).
When publishing or writing a description, follow
[Pull requests](doc/pull-requests.md). When acting as orchestrator, follow
[orchestrator handoffs](doc/orchestrator.md#review-and-return) for agent review
and publication ownership. The maintainer reviews and merges; agents merge
only with explicit maintainer instruction.

After the maintainer confirms a Work PR merged, follow
[post-merge branch cleanup](doc/branch-cleanup.md). Retained branches and GitHub
status queries are not routine Work tracking; use the
[Work lifecycle](doc/workflow.md#lifecycle) for parent status rules.

## Commits and pull requests

For small unrelated fixes or documentation edits, use `fix/`, `docs/`, or
`chore/` branches with short lowercase, hyphen-separated names.

Keep commits focused and use Conventional Commits (Commitizen enforced). Use an
imperative subject, aiming for 50 characters including type and scope. Separate
the body with a blank line; hard-wrap prose and bullet continuations at 72
columns, preserving unbreakable URLs and tokens.

For staged changes, `make commit` formats the optional body with rumdl and runs
ordinary `git commit` with installed hooks. Quote Make inputs in the caller's
shell. For example:

```sh
make commit SUBJECT='fix: describe the change' BODY='Why it matters.'
make commit SUBJECT='fix: describe the change' BODY=$'First line.\nSecond line.'
make commit SUBJECT='fix: describe the change' BODY='Run this command:

    printf "%s\\n" "$HOME"'
```

Four-space indentation marks literal commands and preserves their line breaks;
unmarked prose can reflow.

Rumdl does not preserve Git trailer syntax specially; for example, a long
`Signed-off-by:` line can be split, so do not put trailers in `BODY`.

External contributions are gated pending CLA setup (see [Status](#status)).

## License

Apache 2.0. New source files should carry an SPDX header:

```python
# SPDX-License-Identifier: Apache-2.0
```
