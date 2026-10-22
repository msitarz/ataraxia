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

The post-merge closure parent and its command and adoption Works remain
retained historical records. Their delivered lifecycle guidance remains
identified as delivered; their unfinished command and adoption outcomes are
explicitly superseded and are no longer prerequisites for delivery. Their
unfinished criteria remain `TODO` under the existing criterion syntax. This
disposition does not claim those outcomes were implemented.

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
