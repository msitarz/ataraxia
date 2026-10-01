# 2. Let parent maps track Work lifecycle

Date: 2026-09-30

## Status

Accepted

## Context

Nested Works need visible status in their owning parent. Retained child
directories or remote branch status can avoid parent edits, but split active
status from the hierarchy or depend on GitHub queries for tracking.

## Decision

A parent README owns the status of each immediate child using `TODO`, `DONE`, or
`ABORT`; a child does not duplicate that status. Update the parent map and
remove a completed or abandoned child directory in the same PR. Use PR
discussion and Git for review history instead of retaining journals.

## Consequences

Parent maps require edits when children finish, and integrated status is checked
against `master`. In return, current status stays beside the hierarchy and
finished contracts leave the active guidance tree. See
[Work lifecycle](../workflow.md) and
[PR #60](https://github.com/msitarz/ataraxia/pull/60).
