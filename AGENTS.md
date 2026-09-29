# Repository Guidelines

## Start Every Task Here

Read [doc/ubiquitous-language.md](doc/ubiquitous-language.md) **in full at the start of every task**, before substantive discussion, planning, defining new terms, review, or implementation. Apply its vocabulary throughout. Reread after context loss or compaction and whenever definitions change. Every agent, including subagents, must do this; include the requirement and relevant vocabulary/contract references when delegating.

When defining, implementing, or reviewing a feat slice, read [doc/feat-workflow.md](doc/feat-workflow.md) **in full before starting that work**.

Then inspect task-relevant code, tests, and ADRs. Distinguish current behavior from intended changes and surface discrepancies affecting the task. Before changing architectural boundaries, read [doc/architecture.md](doc/architecture.md) and follow the [ADR workflow](#architecture-decision-records).

## Engineering Conventions

For any repository change, follow
[repair and scope rules](doc/engineering.md#fix-the-underlying-problem).
Read the full [engineering conventions](doc/engineering.md) when changing or
reviewing code or tests.

## Repository Map

Ataraxia is a pre-alpha orchestrator for bar-by-bar trading backtests:

- `src/ataraxia/compute/`: computation graph and loop; sibling modules handle sources, providers, features, brokerage, backtesting, and CLI.
- `test/unit/`, `test/integration/`, `test/acceptance/`: tests by boundary.
- `example/`: crossover strategy and its tests; `sample/`: synthetic CSV data.
- `doc/feat/`: feat slices; [doc/adr/](doc/adr/): architectural decisions.

Execution is currently local, sequential, and single-source. Parallel execution, multi-source synchronization, and immutable artifact storage are planned; verify status in code before treating documents as implemented behavior.

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
- Link to definitions instead of duplicating them; update affected code, tests, and docs together. Follow the [ADR workflow](#architecture-decision-records) for architectural changes.
- Verify meaning and module boundaries through observable examples and tests, including timing, units, state transitions, and failures.

Background: [Thoughtworks](https://www.thoughtworks.com/insights/blog/evolutionary-architecture/domain-driven-design-in-10-minutes-part-one), [Fowler and Joshi](https://martinfowler.com/articles/convo-llm-abstractions.html), [Schleicher](https://www.danielschleicher.com/software/engineering,/ai,/spec-driven/development/2026/01/04/removing-ambiguity-with-spec-driven-development.html).

## Architecture Decision Records

Create an ADR only for a substantive architectural decision. Correcting types, tests, or implementation to conform to an established contract does not require a new ADR. Do not turn recovery from your own mistake into a new architectural decision.

1. Search `doc/adr/` for the problem and related decisions; read relevant records and follow amendment/supersession links. Reuse a covering ADR instead of duplicating it.
2. Record uncovered architectural decisions **before implementing the affected design**, including module boundaries, execution models, resource ownership, and persistent contracts. Recheck when implementation reveals new choices. Create or reuse an issue before non-trivial architectural work.
3. Use the next unused number and `NNNN-kebab-case-title.md`. Format: `# N. Title`, `Date: YYYY-MM-DD`, then `Status`, `Context`, `Decision`, and `Consequences`. Explain the problem, relevant alternatives/tradeoffs, choice, and consequences. Use `Proposed` while unsettled and `Accepted` once decided.
4. Change accepted decisions through new records; preserve earlier context, decision, and consequences. Use relative Markdown links:
   - Partial change: new Status says `Amends [N. Title](NNNN-title.md)`; on acceptance, add reciprocal `Amended by [M. Title](MMMM-title.md)` to the earlier record. Follow ADRs 0010/0011 and state what still applies.
   - Replacement: new Status says `Supersedes [N. Title](NNNN-title.md)`; on acceptance, set earlier status to `Superseded by [M. Title](MMMM-title.md)`, following [adr-tools](https://github.com/npryce/adr-tools).
5. Update slice links and `doc/architecture.md` to reflect the decision and implementation status.

### ADR Writing Style

Match the maintainer's direct, practical voice. Before drafting, reread the closest ADR: 0014 for a small convention, 0012 for a tradeoff, or 0016 for lifecycle changes. Use short sentence-case titles naming the choice and plain, concrete prose; contractions and blunt sentences are natural. Scale detail to the problem, prefer paragraphs, and use lists/code only where useful. Avoid corporate language, inflated benefits, generic introductions, exhaustive templates, and manufactured quirks; keep grammar correct. Compare the draft with its related ADR and remove padding.

- **Context:** explain current behavior and what breaks, becomes awkward, or creates work for the quant. Include useful examples and link relevant prior decisions.
- **Decision:** state the change directly, why, meaningful alternatives, and tradeoffs. Use first person only for the maintainer's stated reasoning; never invent personal history or experiments.
- **Consequences:** state costs, capabilities, drawbacks, and deferred work without repeating vague benefits. One sentence can suffice; use bullets for distinct effects.

## Computation and Strategy Contracts

- Keep `compute/` independent of trading concepts and concrete I/O.
- Preserve stable node equality/hashes; equivalent dependencies share computation. Pass the same source instance through dependent nodes. `SourceNode.factory()` returns the runner updated by `send()` (ADR 0012).
- `compute()` owns the source context; the source delegates resource management to its provider (ADR 0016). Explicitly close the generator when stopping consumption early.
- Strategy modules export a sink class as `__sink__`; backtesting constructs it with a source (ADR 0014).
- Rolling windows return newest first. The broker enters at the signal bar's close and evaluates exits on subsequent bars (ADR 0013). Prices/PnL use ticks, four per point for supported instruments. Preserve these conventions unless explicitly changed by the task.

## Commits and Pull Requests

For small unrelated fixes or documentation edits, use `fix/`, `docs/`, or `chore/` branches with short lowercase, hyphen-separated names.

Keep commits focused and use Conventional Commits (Commitizen enforced). Use an imperative subject, aiming for 50 characters including type and scope. Separate the body with a blank line; hard-wrap prose and bullet continuations at 72 columns, preserving unbreakable URLs and tokens.

Every agent-created commit must include a succinct body with three labeled sections: `Why:`, `What:`, and `How:`, separated by blank lines. Explain the problem or motivation, the resulting change, and the implementation approach, respectively. Keep each section brief and include relevant validation in `How:`. Avoid repeating the subject, listing files, or narrating the work session.

PRs explain the problem, resulting behavior, and validation, with relevant issue links. External contributions are gated pending CLA setup; follow [CONTRIBUTING.md](CONTRIBUTING.md). Determine the PR base from explicit task instructions or repository metadata, consistent with contribution guidance.
