# 2. Let parent maps track Work lifecycle

Date: 2026-09-30

## Status

Accepted

## Context

Nested Works need a visible status in their owning parent. Completed Work
contracts should not become a permanent second tracking system when PRs and Git
preserve the review history.

## Decision

A parent README owns the status of each immediate child using `TODO`, `DONE`, or
`ABORT`; a child does not duplicate that status. Update the parent map and
remove a completed or abandoned child directory in the same PR. Use PR
discussion and Git for review history instead of retaining journals.

## Consequences

Parent maps show current delivery state while active, and finished Work
contracts leave the active guidance tree. See [Work lifecycle](../workflow.md)
and [PR #60](https://github.com/msitarz/ataraxia/pull/60).
