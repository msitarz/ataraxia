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

## Documentation

Read [documentation ownership](doc/documentation.md) when creating, changing,
or reviewing documentation. It owns placement, duplication, and shared-term
maintenance rules.
