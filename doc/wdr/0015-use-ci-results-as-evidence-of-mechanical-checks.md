# 15. Use CI results as evidence of mechanical checks

Date: 2026-10-03

## Status

Accepted

Amends
[6. Keep delivery evidence in PRs and Git](0006-keep-delivery-evidence-in-prs-and-git.md)
for mechanical-check evidence and
[14. Remove mandatory PR records for manual judgment](0014-remove-mandatory-pr-records-for-manual-judgment.md)
for PR review-reporting records. Other decisions remain in force.

Amended by
[21. Publish after local Work acceptance](0021-publish-after-local-work-acceptance.md).

## Context

Agent-written prose about checks can be inaccurate and later mistaken for
verified fact. Later agents may rely on a narrative assertion as though it
were an execution record, allowing an unsupported claim to survive subsequent
review. [PR 135](https://github.com/msitarz/ataraxia/pull/135) adopts a
mechanical evidence boundary and keeps the current PR template. WDR 6 permits
PR discussion as delivery evidence; WDR 14 removes mandatory manual-review
records without prohibiting review-reporting comments.

## Decision

Actual automated execution and results in CI on the latest reviewed PR head
establish mechanical-check outcomes. Required mechanical checks must be covered
by CI. Agent-written summaries, inventories, and review comments cannot
establish that checks passed.

Keep current rules in the [validation owner](../validation.md) and PR format
and publication rules in the [PR owner](../pull-requests.md). Preserve the
Purpose, Outcome, and Limitations template, exclude evidence inventories from
PR descriptions, and do not add PR comments or discussion to record review or
report checks.

Independent review remains required for judgments CI cannot establish. This
decision does not prohibit Investigation conclusions, explanations, or actual
artifacts. It preserves the retained Work contract and separate cleanup commits,
maintainer review and merge authority, and the full latest-head CI gate.

## Consequences

Reviewers inspect CI execution and results rather than treating prose as proof
of passing checks. Local focused checks remain useful preparation, but do not
replace latest-head CI evidence or the merge gate. Manual judgment retains
independent review without a PR reporting obligation. Existing accepted history
remains intact.
