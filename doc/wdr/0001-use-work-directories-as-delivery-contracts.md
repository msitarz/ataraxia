# 1. Use Work directories as delivery contracts

Date: 2026-09-30

## Status

Accepted

## Context

A Work needs an observable outcome and acceptance criteria so its reviewer can
tell when it is complete. The contract should stay discoverable at the Work's
repository path.

## Decision

Identify a Work by its repository directory and short README contract. Add
`spec.md` or `design.md` only when useful. Choose this flexible contract over a
mandatory multi-document template: simple Works avoid unused process, at the
cost of less uniform structure.

## Consequences

Scope and acceptance live beside the Work, while PR discussion and Git preserve
the review history. See [Work contracts](../workflow.md) and
[PR #59](https://github.com/msitarz/ataraxia/pull/59).
