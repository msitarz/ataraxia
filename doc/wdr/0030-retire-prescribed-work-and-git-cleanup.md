# 30. Retire prescribed Work and Git cleanup

Date: 2026-10-22

## Status

Accepted

Supersedes
[18. Delegate verified post-merge cleanup to cleaner](0018-delegate-verified-post-merge-cleanup-to-cleaner.md)
for required cleaner dispatch,
[28. Retain Work contracts until authorized closure](0028-retain-work-contracts-until-authorized-closure.md)
for contract removal as a delivery step, and
[29. Publish authorized Work closure on the reviewed PR](0029-publish-authorized-work-closure-on-the-reviewed-pr.md)
for the planned closure command and its post-merge cleanup route. Maintainer
review, merge authority, independent review, and full CI on the final reviewed
head remain in force.

Amends
[20. Route agents by responsibility](0020-route-agents-by-responsibility.md)
for retiring Cleaner routing; Definer, Executor, and Publisher routing and the
remaining role, review, and model-selection policies remain unchanged.

## Context

Current guidance prescribed removing selected Work contracts through a closure
publication flow and removing merged branches and worktrees through a cleaner
procedure. The command and adoption Works for that flow remain unfinished.
Maintainers want to handle cleanup manually and observe its evolution before
deciding whether another process is useful. Completed Works, supporting
artifacts, and architecture records must remain available through the parent
Work's completion; maintainers may remove retained records manually later.

## Decision

Work completion does not require removing contracts, supporting artifacts,
branches, or worktrees. Current guidance retains Work contracts and supporting
artifacts after completion and does not prescribe a closure command, cleaner
role, or post-merge branch/worktree procedure. Maintainers handle any cleanup
manually. This decision creates no replacement cleanup process or automation.
Safe low-level Git and worktree tools remain available for ordinary use.

The maintainer later authorized deletion of exactly the post-merge closure
parent, command, and adoption contracts through the cleanup retirement Work.
Those three files are removed from the current tree; Git history preserves
their prior states. The lifecycle guidance was delivered, while the command
and adoption outcomes were unfinished and were never implemented. This
deletion does not authorize removing other Works or artifacts and does not
change Work discovery, checks, or criterion parsing.

## Consequences

Contracts and supporting artifacts stay inspectable in the repository after
completion. The maintainer decides manually whether and when to remove them.
Review, merge, and final-head CI gates are unchanged. Cleanup may evolve through
maintainer experience before any later decision establishes another process.

Current retention guidance lives in
[Work workflow](../workflow.md#lifecycle) and
[Work acceptance](../acceptance-tracing.md#work-delivery). Current delegation
and contribution routes live in
[orchestrator guidance](../orchestrator.md#roles-and-delegation) and
[contributor guidance](../../CONTRIBUTING.md#work-branches-review-and-merge).
The retired [branch cleanup](../branch-cleanup.md) page is retained as a
historical notice. This decision and its implementation are carried by the
[cleanup retirement Work](../feat/outcome-driven-guidance/retire-cleanup/README.md).
