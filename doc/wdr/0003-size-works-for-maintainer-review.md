# 3. Size Works for maintainer review

Date: 2026-10-01

## Status

Accepted

## Context

The maintainer identified their understanding and review capacity as the
bottleneck. A Work that takes too long to understand holds up steering and
manual review.

## Decision

Give each leaf Work one responsibility and an outcome that takes about five
minutes to review. Nest independent responsibilities instead of accumulating
scope. An explicit maintainer request may add scope to the current PR for
steering, but the ordinary manual review and merge gates still apply.

## Consequences

Work boundaries protect review time while leaving the maintainer able to steer
an active PR. See [Work scope and sizing](../workflow.md#scope-and-sizing),
[contribution review gates](../../CONTRIBUTING.md#work-branches-review-and-merge),
[PR #62](https://github.com/msitarz/ataraxia/pull/62), and
[PR #80](https://github.com/msitarz/ataraxia/pull/80).
