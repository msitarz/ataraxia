# Repository Guidelines

## Start Every Task Here

Read [doc/ubiquitous-language.md](doc/ubiquitous-language.md) **in full at the start of every task**, before substantive discussion, planning, defining new terms, review, or implementation. Apply its vocabulary throughout. Reread after context loss or compaction and whenever definitions change. Every agent, including subagents, must do this; include the requirement and relevant vocabulary/contract references when delegating.

When defining, implementing, or reviewing a feat slice, read [doc/feat-workflow.md](doc/feat-workflow.md) **in full before starting that work**.

Then inspect task-relevant code, tests, and ADRs. Read
[doc/architecture.md](doc/architecture.md) for the repository map and current
computation and backtesting contracts. Distinguish current behavior from intended
changes and surface discrepancies affecting the task. Before changing
architectural boundaries, follow the [ADR workflow](doc/adr-workflow.md).

## Engineering Conventions

For any repository change, follow
[repair and scope rules](doc/engineering.md#fix-the-underlying-problem).
Read the full [engineering conventions](doc/engineering.md) when changing or
reviewing code or tests.

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

## Ubiquitous Language

The [glossary](doc/ubiquitous-language.md) is the single source of truth for shared definitions; feat slices own local rules. Use its terms consistently and reuse abstractions when their meaning fits.

- Keep concepts distinct; a runner is not an executor worker. Use "feat slice" as defined in the glossary, keeping it distinct from a trading Feature. Qualify terms and explain boundary mappings.
- Resolve ambiguity from the request and repository. If meanings still imply materially different behavior, present concrete interpretations to the user before implementation. Do not invent domain rules; naming consistent with established meanings needs no confirmation.
- Check for an existing term before introducing one. Define needed terms in the glossary **before using them in specifications or implementation**: meaning, responsibility, distinctions, relationships, and relevant units or lifecycle rules.
- Link to definitions instead of duplicating them; update affected code, tests, and docs together. Follow the [ADR workflow](doc/adr-workflow.md) for architectural changes.
- Verify meaning and module boundaries through observable examples and tests, including timing, units, state transitions, and failures.

Background: [Thoughtworks](https://www.thoughtworks.com/insights/blog/evolutionary-architecture/domain-driven-design-in-10-minutes-part-one), [Fowler and Joshi](https://martinfowler.com/articles/convo-llm-abstractions.html), [Schleicher](https://www.danielschleicher.com/software/engineering,/ai,/spec-driven/development/2026/01/04/removing-ambiguity-with-spec-driven-development.html).

## Commits and Pull Requests

For small unrelated fixes or documentation edits, use `fix/`, `docs/`, or `chore/` branches with short lowercase, hyphen-separated names.

Keep commits focused and use Conventional Commits (Commitizen enforced). Use an imperative subject, aiming for 50 characters including type and scope. Separate the body with a blank line; hard-wrap prose and bullet continuations at 72 columns, preserving unbreakable URLs and tokens.

Every agent-created commit must include a succinct body with three labeled sections: `Why:`, `What:`, and `How:`, separated by blank lines. Explain the problem or motivation, the resulting change, and the implementation approach, respectively. Keep each section brief and include relevant validation in `How:`. Avoid repeating the subject, listing files, or narrating the work session.

PRs explain the problem, resulting behavior, and validation, with relevant issue links. External contributions are gated pending CLA setup; follow [CONTRIBUTING.md](CONTRIBUTING.md). Determine the PR base from explicit task instructions or repository metadata, consistent with contribution guidance.
