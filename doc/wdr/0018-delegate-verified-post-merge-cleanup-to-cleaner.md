# 18. Delegate verified post-merge cleanup to cleaner

Date: 2026-10-10

## Status

Accepted

## Context

Post-merge worktree and branch removal is a state-changing operation governed
by [branch-cleanup guidance](../branch-cleanup.md). A distinct operational role
keeps those removals separate from Work leaf implementation while preserving
maintainer control. This role and its scope were defined in the
[cleanup guidance Work](https://github.com/msitarz/ataraxia/blob/0905496f4e3fb6233d655cae7316a981de2dfc57/doc/feat/delegated-cleanup/guidance/README.md).

The task-specific maintainer authorization uses Luna at medium effort for
cleaner work only. The leaf-executor model policy in
[WDR 13](0013-use-sol-low-for-all-leaves.md) remains unchanged. No measured
reduction in orchestrator effort or cost is established.

## Decision

After the maintainer confirms a Work PR merged, the orchestrator may hand
verified post-merge cleanup to the reusable `cleaner` operational role. The
cleaner follows the existing procedure and guardrails in
[branch-cleanup guidance](../branch-cleanup.md), reports its checks and
comparisons, removals, and blockers, and stops on failure or uncertainty. The
orchestrator reviews that report rather than repeating the operations.

Serialize cleanup with worktree creation and other shared Git mutations. The
cleaner role does not implement Work changes, publish or review PRs, merge code,
or recursively delegate. Maintainer review, merge authority, and latest-head
full-CI requirements for delivery remain in force.

## Consequences

The operational handoff and verification owner are explicit without changing
Work leaf policy or existing cleanup safety. Any benefit to orchestrator effort
remains a hypothesis for the separate operational trial.
