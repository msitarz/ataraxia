# Work contracts

Read this file when creating, changing, or reviewing a Work.

Each Work lives in a directory identified by its repository path. Its short
`README.md` states the intended outcome and observable acceptance criteria so
the reviewer can tell when it is complete. Add `spec.md` or `design.md` only
when useful, and link to it from the README.

Explain the problem and verified current behavior when relevant. Define
completion with observable examples, including preconditions, action, and
expected outcomes; cover boundaries, failures, or behavior to preserve when
they matter. State scope, non-goals, dependencies, assumptions, and open risks
as useful, separating required contracts from provisional design. Use an
[Investigation](#investigations) or [Prototype](#prototypes-and-rewrites) when
feasibility needs checking. For performance claims, give a representative
workload, baseline, measurement method, and success threshold. Scale detail to
the Work; these are prompts, not mandatory fields or headings.

Use standard relative Markdown links. Use Mermaid when a diagram helps explain
behavior, relationships, or design choices; small changes do not need one.

Do not require fixed headings, YAML frontmatter, a journal, or separate
human-facing and agent-facing versions of the same contract.

## Scope and sizing

Give each leaf Work one responsibility and an outcome a maintainer can
understand and review quickly, aiming for about five minutes of human review.
When a Work would accumulate unrelated responsibilities or take longer to
understand, nest independently reviewable child Works under a parent that maps
their outcomes. Do not push additional scope into a leaf just because it is
nearby. An explicit maintainer request may add scope to the current Work PR so
the maintainer can steer that revision; the ordinary manual review and merge
gates still apply, and the request does not waive the maintainer's manual
review or merge decision.

## Lifecycle

A parent README maps its immediate child Works. `TODO` links to an active
child's README, `DONE` names the delivered outcome, and `ABORT` records why the
Work stopped. The child does not duplicate its parent-owned status.
Status entries describe the checked-out branch; use `master` to determine
integrated status. Merge a parent map to `master` before starting child PRs that
edit it.

Delivery or abandonment updates the parent's entry and removes the finished
child directory in the same PR. Before removing a finished Work, promote
lasting contracts and decisions to their authoritative owners. PRs hold review
discussion; Git preserves removed contracts and exact changes.

Before completing a Work, review tests added during it. Read
[test ownership](test-ownership.md) when completing a Work.

Discovery may add children without maintaining a fixed execution list. Nest
when it reduces necessary context; strongly discourage more than five levels.
Directory ancestry does not select a Git base.

## Investigations

An Investigation produces a recommendation for a bounded question. Its README
states the question, constraints, and decision needed. For each serious
candidate, record its fit for the problem, pros and cons, and what was checked
versus what remains uncertain. Conclude with a short comparison and
recommendation that explains the choice.

Use one file for a small comparison; use linked candidate files when they make
review easier. A supporting Prototype can answer a question that documentation
alone cannot resolve. An Investigation recommends a direction; a Prototype
demonstrates feasibility through exploratory implementation.

Follow the common Work lifecycle and review rules. On completion, promote the
chosen policy or lasting decision to its authoritative owner. Git and the PR
preserve the comparison artifacts when the finished Work directory is removed.
Do not introduce a separate lifecycle or mandatory template.

## Prototypes and rewrites

A Prototype answers a bounded question through exploratory implementation.
Its Work contract states the question, limits, and observable
evidence needed to answer it. Record the result in the PR, including when the
Prototype is unsuccessful, and distinguish observed evidence from assumptions.

Promote a Prototype to production Work only after reviewing missing contracts
and integration requirements. Prototype completion does not imply production
readiness.

A rewrite's contract states behavior to preserve, intended changes, comparison
evidence, cutover, and retirement requirements. Split Prototypes and rewrites
into small, independently reviewable Works when needed.

See
[CONTRIBUTING.md's Work review rules](../CONTRIBUTING.md#work-branches-review-and-merge)
for branch and PR exceptions. Do not introduce a separate tracking system,
journal, or mandatory template.

When acting as orchestrator for repository changes, follow the
[Orchestrator handoffs](orchestrator.md).

When a Work proposes or reviews a consequential delivery-workflow choice,
follow the [WDR workflow](wdr-workflow.md). Routine Work tasks do not need to
read it.
