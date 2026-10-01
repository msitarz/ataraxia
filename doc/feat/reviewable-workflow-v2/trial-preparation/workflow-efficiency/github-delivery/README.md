# GitHub delivery

Define a reviewable Work delivery sequence in the stable
[acceptance-tracing owner](../../../../../acceptance-tracing.md) and
[contributor guidance](../../../../../../CONTRIBUTING.md#work-branches-review-and-merge).
Coordinate shared owners and prerequisites through the
[parent map](../README.md#works); local artifact review and PR-description
ownership remain with the orchestrator under the mapped
[handoffs outcome](../README.md#works).

The integrated [PR 108](https://github.com/msitarz/ataraxia/pull/108) provides
a delivery observation: its rebased branch preserved an implementation
commit with the verified Work contract and evidence
([`c8cfad8`](https://github.com/msitarz/ataraxia/commit/c8cfad8)) before a
separate cleanup commit
([`582a4b8`](https://github.com/msitarz/ataraxia/commit/582a4b8)). The matching
tree comparisons were verified. This records a workable evidence-preserving
sequence, not a performance claim.

Plan one reviewable delivery protocol for a Work with acceptance criteria:

1. Before final review, retain an implementation commit containing the Work
   contract with verified criteria marked `DONE` and their evidence beside
   them where needed. Development fixups may be folded into this snapshot;
   preserving every intermediate commit or SHA is not required.
2. Add a separate cleanup commit removing the completed Work and updating its
   parent map. Keep regression tests under their existing test owner. The
   implementation/evidence snapshot must remain an ancestor of the cleanup
   commit.
3. Rebase the completed sequence onto current `master` while preserving both
   snapshots in linear history. If the branch was already published, the
   owning orchestrator publishes the rewrite with `--force-with-lease` against
   the expected remote head, refreshes evidence links, then reviews the final
   head and waits for its required full CI results.
4. Require explicit maintainer authorization for the final merge. Agents do
   not merge autonomously; they may merge only with that explicit instruction.
   Do not change repository settings, use an admin override, or bypass review
   or CI gates to make the sequence work.

Current GitHub observations for this repository are rebase merge enabled,
required approval disabled for its single-maintainer configuration, and
required CI gates retained. GitHub does not allow an author to approve their
own PR; the local workflow still requires human review. These observations do
not authorize an administrator override or branch-policy change.
Preserve accepted WDR9; if delivery changes its decision, follow the
[WDR lifecycle](../pr-evidence/README.md) rather than silently editing the
accepted record.

## Acceptance

- **AC-1 TODO** The delivery contract keeps a verified Work/evidence snapshot
  before a distinct cleanup commit, permits development fixups, and preserves
  both snapshots through a rebase without requiring every intermediate SHA.
  Verification: walk through a Work delivery with a correction, completed
  criteria, cleanup, and regression tests, then inspect the two-commit order.
- **AC-2 TODO** A published rewrite uses the expected remote head, refreshes
  evidence references, and receives final-head review and required CI before
  merge consideration.
  Verification: walk through an already-published branch with a changed base
  and verify stale-head protection, updated links, review, and CI gates.
- **AC-3 TODO** The delivery distinguishes GitHub merge settings from local
  human-review and maintainer-merge requirements; agents merge only with
  explicit maintainer instruction and do not change settings, use admin
  overrides, or bypass gates.
  Verification: inspect the documented settings and walk through an author
  PR where approval is unavailable to the author but human review and explicit
  maintainer merge authorization remain required.
