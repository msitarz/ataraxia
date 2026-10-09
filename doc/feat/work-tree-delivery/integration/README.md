# Integrate recursive subtrees and publish once

After sequential guidance, own recursive scheduling/integration at
[orchestrator guidance](../../../orchestrator.md), with a compact Mermaid
diagram there; link [Work workflow](../../../workflow.md),
[acceptance tracing](../../../acceptance-tracing.md) and
[PR publication](../../../pull-requests.md) for their procedures rather than
duplicating them. Each child parent owns its orchestrator and executor, with a
separate isolated worktree and assigned base ref. Independent subtrees may run
in parallel when dependencies, capacity and shared edits permit; direct leaves
remain sequential within their owner. Executors do not recursively delegate.

Parent review owns interfaces/integration and reuses leaf evidence. Retain a
child-parent contract through that integration review; its parent owner records
verified child cleanup and the parent-map update afterward. Preserve linear
verification/cleanup history while integrating subtree commits. The top
requested-Work owner alone publishes its final reviewed branch/description;
requested child parents do not publish independently. One final PR covers the
entire requested Work, with full CI on its reviewed final head and maintainer
merge authority. Material corrections keep the existing recovery/review gates.

Reconcile conflicting branch/base, child-PR/map and whole-diff publication
wording only at its current owners, including CONTRIBUTING when necessary. The
five-minute assessment applies to complete leaves; integrated parent review
still assesses interfaces and preserves substantive scope requirements.
Reserve/index WDR22, amending WDR12 for execution/integration ownership and
WDR21 for requested-tree publication, with reciprocal metadata in the same
adoption. Preserve accepted history and reserved WDR18/19/20 model/operational
Works. No claimed speed/cost benefit from #257, new tools or model-policy
changes.

- **AC-1 TODO** Given dependency-ready child parents and reviewed leaf
  histories, guidance integrates parallel isolated subtrees with correct
  retained contracts, parent-owned maps and one top-owner publication without
  weakened review, evidence, final-head CI or maintainer control.

  Validation: manually trace nested integration, shared-edit sequencing, a
  paused subtree and final publication; inspect diagram, owner/branch routes,
  WDR22 index/amendments and linear contract history, then run doc/ac checks.
