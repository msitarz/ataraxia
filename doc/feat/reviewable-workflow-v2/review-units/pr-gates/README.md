---
id: pr-gates
---

# PR review and merge gates

Give each unit a branch and small PR to its parent branch. The PR owns checks,
discussion, and rationale; the maintainer reviews its current revision and
performs merges. A parent direction and material contract changes need explicit
approval. Small children within that direction can proceed to their own review.

The parent branch can merge to `master` at a releasable checkpoint, then remain
for later work through a new PR. Use local Git merge history for child completion
and preserve merge commits while the parent is active, without status fields in
READMEs or repeated GitHub lookups. GitHub-approved or
manually merged PRs provide durable decisions across sessions; an available
conversation can supply the current session's approval.
