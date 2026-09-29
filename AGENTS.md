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

## Contribution and Validation

Follow [CONTRIBUTING.md](CONTRIBUTING.md) for setup, commands, validation,
branches, commits, and PRs. The [Makefile](Makefile) defines executable checks;
the [CI workflow](.github/workflows/ci.yml) invokes its shared targets.

## Ubiquitous Language

The [glossary](doc/ubiquitous-language.md) is the single source of truth for shared definitions; feat slices own local rules. Use its terms consistently and reuse abstractions when their meaning fits.

- Keep concepts distinct; a runner is not an executor worker. Use "feat slice" as defined in the glossary, keeping it distinct from a trading Feature. Qualify terms and explain boundary mappings.
- Resolve ambiguity from the request and repository. If meanings still imply materially different behavior, present concrete interpretations to the user before implementation. Do not invent domain rules; naming consistent with established meanings needs no confirmation.
- Check for an existing term before introducing one. Define needed terms in the glossary **before using them in specifications or implementation**: meaning, responsibility, distinctions, relationships, and relevant units or lifecycle rules.
- Link to definitions instead of duplicating them; update affected code, tests, and docs together. Follow the [ADR workflow](doc/adr-workflow.md) for architectural changes.
- Verify meaning and module boundaries through observable examples and tests, including timing, units, state transitions, and failures.

Background: [Thoughtworks](https://www.thoughtworks.com/insights/blog/evolutionary-architecture/domain-driven-design-in-10-minutes-part-one), [Fowler and Joshi](https://martinfowler.com/articles/convo-llm-abstractions.html), [Schleicher](https://www.danielschleicher.com/software/engineering,/ai,/spec-driven/development/2026/01/04/removing-ambiguity-with-spec-driven-development.html).
