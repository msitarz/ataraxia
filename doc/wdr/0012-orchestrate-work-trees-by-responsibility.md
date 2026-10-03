# 12. Orchestrate Work trees by responsibility

Date: 2026-10-02

## Status

Accepted

Amended by
[13. Use Sol-low for all leaves](0013-use-sol-low-for-all-leaves.md).

Amends
[4. Delegate repository changes for independent review](0004-delegate-repository-changes-for-independent-review.md).
WDR 4's low-effort leaf execution, no same-task recursive delegation,
independent orchestrator review, and maintainer control remain in force.

## Context

The earlier per-leaf wrapper arrangement added a dedicated Sol layer around each
Luna leaf. Work nodes already provide responsibility boundaries, and the parent
or subtree owner needs to integrate its children. The two reported experiments
are not controlled comparisons: the first nested batches took about 34 minutes
([PR 105](https://github.com/msitarz/ataraxia/pull/105) and
[PR 106](https://github.com/msitarz/ataraxia/pull/106)); the second took about
38 minutes ([PR 107](https://github.com/msitarz/ataraxia/pull/107) and
[PR 108](https://github.com/msitarz/ataraxia/pull/108)). The later WDR-status
and index revisions are recorded at
[#107 revision c48b366](https://github.com/msitarz/ataraxia/commit/c48b3663e32c59862ef7cfc5b761fc6a9fcdbd8e)
and
[#108 revision 2bbdd12](https://github.com/msitarz/ataraxia/commit/2bbdd12d8fd39827b8f5650a6db0f211e3ee325f).
Reported observations also include delayed launches and about 13 seconds of
initial overlap despite available slots, about 11 minutes to draft PR evidence,
shared-file conflicts, and formatting rework. They span different scopes and do
not establish causal attribution or a topology speedup. Token cost and actual
human review time remain unavailable. This Work carries the change:
[Workflow efficiency](../feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/README.md).

## Decision

The orchestrator that owns a Work node with children owns planning and
integration for that subtree and manages its immediate child agents. Delegate
each leaf directly to Luna, with its owning parent as
the single responsible reviewer. A child node with children owns its own
subtree orchestration. Do not add a dedicated Sol wrapper around a leaf by
default. Work nodes mark responsibility boundaries, not required runtime
layers. Parent and subtree reviews own integration and interfaces and reuse
leaf check evidence instead of repeating a full leaf review. Schedule by
dependency readiness, available concurrency, and expected shared edits rather
than launching the entire tree at once. Do not invent intermediary Work nodes
solely to justify runtime layers.

Every leaf executor creates and uses an isolated Git worktree before editing.
The handoff names its destination path and branch and gives the command.
Preserve independent review, maintainer approval for model or effort changes,
human merge control, and full CI gates.

## Consequences

Separate Work responsibilities can be delegated directly to leaf executors
while each subtree retains a clear integration and review owner. This removes
the default extra wrapper handoff, while placing direct leaf coordination and
review load on the owning orchestrator. A dedicated wrapper could isolate that
load, but adds a handoff and another responsibility layer. Dependency-aware
scheduling accounts for shared edits and concurrency. The reported experiments
motivate this arrangement but do not prove it is faster; future comparisons
should record comparable dispatch, completion, preparation, correction, and
human-review measurements when available. Current rules belong in
[orchestrator handoffs](../orchestrator.md). This amends WDR 4 only to define
Work-tree ownership and routing; its other requirements remain unchanged.
