# 1. Use Work directories as delivery contracts

Date: 2026-09-30

## Status

Accepted

## Context

A Work needs an observable outcome and acceptance criteria so its reviewer can
tell when it is complete. The contribution workflow also needs a durable review
path without requiring a separate issue for every Work.

## Decision

Identify a Work by its repository directory and short README contract. Add
`spec.md` or `design.md` only when useful; do not require fixed headings,
frontmatter, or a journal. Work PRs use branches and PR discussion without
routine issues. Keep issues available for bugs and human collaboration.

## Consequences

Scope and acceptance live beside the Work. The PR carries review discussion and
Git preserves its history. See [Work contracts](../workflow.md) and
[contribution rules](../../CONTRIBUTING.md), established in
[PR #57](https://github.com/msitarz/ataraxia/pull/57) and
[PR #59](https://github.com/msitarz/ataraxia/pull/59).
