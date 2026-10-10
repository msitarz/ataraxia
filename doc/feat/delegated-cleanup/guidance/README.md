# Cleanup role guidance and WDR

Update the post-merge cleanup owner and orchestrator route for a distinct
reusable subagent named `cleaner`, using Luna at medium effort as
explicitly authorized for this operational role. The role is not a Work leaf
executor and does not publish PRs, review or merge code, or delegate
recursively.

After the maintainer confirms a Work PR merged, the orchestrator hands off the
PR, branch, worktree, reviewed head, and merge IDs. The cleaner agent refreshes
Git objects with `git fetch` before comparisons; checks local and remote tips
separately for changes beyond the reviewed revision; checks for dependent PRs,
dirty or untracked state, and uncertain comparisons; then follows all existing
branch-cleanup guardrails. It removes only the named, verified worktree and
branches, from a surviving worktree. It preserves unrelated state, stops and
reports failures or uncertainty without retrying or bypassing permission, and
returns concise checks, comparisons, removals, and blockers. The orchestrator
assesses that report instead of repeating cleanup operations. Serialize cleanup
with worktree creation and other shared Git mutations.

The delivery also adds and indexes WDR 18 to record the rationale and
boundaries. Treat cleanup as an operational role distinct from Work leaf
execution; the explicitly authorized model and effort apply only to this role
and do not change general leaf policy. Keep current rules in
`doc/branch-cleanup.md` and `doc/orchestrator.md`, retain all existing
guardrails, and preserve maintainer review, merge, and full-CI gates for
documentation delivery. Treat reduced token or orchestrator cost as a
hypothesis, not a measured benefit or superiority claim.

- **AC-1 DONE** Given a maintainer-confirmed merged PR and complete handoff,
  guidance defines safe verification, scoped cleanup, stop/report behavior,
  serialized shared-Git operations, and concise orchestration without weakening
  existing cleanup or delivery authority.

  Validation: manually inspect the revised authoritative guidance and WDR 18
  against every existing branch-cleanup guardrail and current orchestration,
  Work, WDR, and PR ownership rules.
