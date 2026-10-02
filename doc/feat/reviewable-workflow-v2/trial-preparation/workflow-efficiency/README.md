# Workflow efficiency

Refine how bounded workflow changes are handed off, evidenced, and prepared,
using the two completed nested-agent experiments as observations rather than a
controlled comparison of topologies.

The agent-reported first nested batch took about 34 minutes from dispatch to
final handoff ([PR 105](https://github.com/msitarz/ataraxia/pull/105) and
[PR 106](https://github.com/msitarz/ataraxia/pull/106)); the second took about
38 minutes ([PR 107](https://github.com/msitarz/ataraxia/pull/107) and
[PR 108](https://github.com/msitarz/ataraxia/pull/108)). They covered different
Works, so the timings do not establish a speedup. In the latest session, seven
total slots removed slot waiting, while initial executor phases still
overlapped by about 13 seconds (their starts were 3 minutes 25 seconds apart).
Drafting completion PR evidence took about 11 minutes. These are reported
observations, not a cost model.

In the second experiment, Sol reused Luna's checks and ran no Make validation.
The orchestrator checked the combined documentation and declarations; CI
remained mandatory. Three shared-document merge conflicts and overly long,
source-wrapping instructions caused extra corrections. Setup included broader
hook and build preparation than documentation work needed, but available
evidence does not show that setup dominated elapsed time. Token cost and actual
human review duration were unavailable.

For the later #107/#108 WDR-status and index amendment, one direct Luna session
handled both worktrees sequentially without an intermediate Sol. The result was
assessed as correct (9/10); efficiency was rated 5/10. Both amended heads passed
full CI ([#107](https://github.com/msitarz/ataraxia/actions/runs/36914292980),
[#108](https://github.com/msitarz/ataraxia/actions/runs/36914277725)); root
reused Luna's local check evidence. Each PR accumulated three commits. The work
also needed an avoidable shared-index introduction correction, repeated
documentation checks after revisions, repeated PR-description edits, and an
early delegated metadata edit. Each branch added an Accepted index entry from
the same base, so after the first merge the other branch must rebase and
integrate the index. See the
[latest #107 revision](https://github.com/msitarz/ataraxia/commit/c48b3663e32c59862ef7cfc5b761fc6a9fcdbd8e)
and
[#108 revision](https://github.com/msitarz/ataraxia/commit/2bbdd12d8fd39827b8f5650a6db0f211e3ee325f).
These are qualitative observations: no exact elapsed time, token use, or cost
was recorded for this small update. They do not establish a controlled
comparison or prove a flatter topology is faster.

Review of the
[latest #107](https://github.com/msitarz/ataraxia/commit/c48b3663e32c59862ef7cfc5b761fc6a9fcdbd8e)
and
[#108](https://github.com/msitarz/ataraxia/commit/2bbdd12d8fd39827b8f5650a6db0f211e3ee325f)
revisions also found repeated explanations inside existing owners despite the
current [documentation review rule](../../../../README.md#review). This points
to an application gap and missing whole-section instruction, not an absent
general duplication rule.

## Works

- **TODO** [Handoffs](handoffs/README.md): improve scope, delegation, parallel
  work selection, and artifact review.
- **TODO** [PR evidence](pr-evidence/README.md): clarify useful completion
  evidence while preserving criterion coverage.
- **TODO** [GitHub delivery](github-delivery/README.md): define a reviewable
  Work commit sequence, preserved acceptance evidence, and safe PR publication
  and merge boundaries.
- **TODO** [Workspace preparation](workspace-preparation/README.md): measure
  minimal preparation or safe reuse for docs-only agent workspaces.
- **TODO** [Tree orchestration](tree-orchestration/README.md): define
  orchestration roles and review ownership for Work trees.
- **TODO** [Guidance editing](guidance-editing/README.md): review surrounding
  guidance as a whole and consolidate repeated explanations within owners.
- **TODO** [Guidance application](guidance-application/README.md): investigate
  consistent application in fresh and long-running sessions.
- **TODO** [Guidance format](guidance-format/README.md): compare itemized and
  paragraph formats for applying semantically equivalent guidance.
- **TODO** [Leaf-agent selection](leaf-agent-selection/README.md): investigate
  when documentation and code leaf tasks warrant Luna low, Luna medium, or Sol
  low.
- **TODO** [Leaf-session reuse](leaf-session-reuse/README.md): compare keeping
  one leaf executor through corrections with replacing it at each correction.
- **TODO** [Single-agent execution](single-agent-execution/README.md): compare
  direct execution with the current orchestrator-to-executor topology.

Use the already authorized direct parent-to-Luna arrangement at low effort at
each leaf boundary; nodes with children have an orchestrator owner. Preserve
independent review and existing human review, merge, and CI gates.

## Comparison

Use the existing [trial contract](../trial-contract/README.md) as evaluation
owner. Before the next comparison, state the scope, measurement method, and
success or reconsideration basis. Record dispatch, executor start, completed
artifact, and PR-ready times; commit batches; PR-description edits; corrections
and their causes; avoidable repeated checks; reporting and preparation effort;
human interventions; and human review time or cost when available. Put concise
results in existing PR evidence or the trial contract, without a per-revision
journal or template.

Separate observed outcomes from candidate rules and note missing or
incomparable measurements. Do not infer a topology speedup from these
differently sized Works.

## Acceptance

- **AC-1 TODO** Handoff and tree-orchestration guidance assign one owner per
  subtree and leaf, while retaining worktree isolation, evidence reuse,
  local executor artifacts, owning-orchestrator PR responsibility, independent
  review, and human and CI gates.
  Verification: inspect the owner guidance and walk through a bounded tree
  with a direct leaf handoff and a child orchestrator.
- **AC-2 TODO** PR evidence guidance covers CI-covered, manual, and removed
  contract cases, accounts for every criterion, and reports failures, pending,
  unrun, and material limitations accurately.
  Verification: walk through
  all three cases against completion evidence and a PR after contract removal.
- **AC-3 TODO** Workspace preparation guidance has a measured minimal path or
  evidence-based reuse approach without unchecked mutable virtual-environment
  sharing, and preserves locked dependencies, stale/missing failures, actual
  consumer setup, and offline/full-audit guarantees.
  Verification: inspect
  the Make-owned path and compare cold/warm preparation where meaningful.
- **AC-4 TODO** A bounded comparison records the observations listed above,
  separates facts from proposed rules, and states limitations without claiming
  that the two different Works prove a speedup.
  Verification: review the
  next iteration's existing PR evidence or trial-contract record against the
  declared basis and available measurements.
- **AC-5 TODO** All mapped child Works are integrated and the bounded
  comparison is captured before this parent is completed.
  Verification: check `master` status for each mapped child and inspect the
  comparison record.
- **AC-6 TODO** The existing documentation review owner requires a whole-section
  pass and consolidation within owners while preserving distinct requirements,
  routes, anchors, and useful examples.
  Verification: walk through the bounded #107 return/recovery and #108
  acceptance-guidance examples after integration, checking retained
  requirements and valid reading routes.
