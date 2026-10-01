# Workflow efficiency

Refine how bounded workflow changes are handed off, evidenced, and prepared,
using the two completed nested-agent experiments as observations rather than a
controlled comparison of topologies.

The first nested batch took about 34 minutes from dispatch to final handoff;
the second took about 38 minutes. They covered different Works, so the timings
do not establish a speedup. In the latest session, seven total slots removed
slot waiting, while initial executor phases still overlapped by about 13
seconds (their starts were 3 minutes 25 seconds apart). Drafting completion PR
evidence took about 11 minutes. These are observed durations, not a cost model.

In the second experiment, Sol reused Luna's checks and ran no Make validation.
The orchestrator checked the combined documentation and declarations; CI
remained mandatory. Three shared-document merge conflicts and overly long,
source-wrapping instructions caused extra corrections. Setup included broader
hook and build preparation than documentation work needed, but available
evidence does not show that setup dominated elapsed time. Token cost and actual
human review duration were unavailable.

## Works

- **TODO** [Handoffs](handoffs/README.md): improve scope, delegation, parallel
  work selection, and artifact review.
- **TODO** [PR evidence](pr-evidence/README.md): clarify useful completion
  evidence while preserving criterion coverage.
- **TODO** [Workspace preparation](workspace-preparation/README.md): measure
  minimal preparation or safe reuse for docs-only agent workspaces.

The parent owns this child map. The three children have no separate status.
Apply the already authorized flat parent-to-Luna, low-effort arrangement to
the next bounded workflow change; the orchestrator reviews independently and
the human retains review and merge decisions. Existing CI remains a gate.

## Comparison

Use the existing [trial contract](../trial-contract/README.md) as evaluation
owner. Before the next comparison, state the scope, measurement method, and
success or reconsideration basis. Record dispatch, executor start, completed
artifact, and PR-ready times; corrections and their causes; avoidable repeated
checks; reporting and preparation effort; human interventions; and human
review time or cost when available. Put concise results in existing PR
evidence or the trial contract, without a per-revision journal or template.

Separate observed outcomes from candidate rules. Note missing or incomparable
measurements, and do not infer a topology speedup from these differently sized
Works. Complete this Work only after the three child outcomes are integrated
and a bounded comparison is captured; defining criteria or check methods alone
does not complete it.

## Acceptance

- **AC-1 TODO** Handoff guidance reflects the scoped findings while retaining
  worktree isolation, consolidated review, evidence reuse, and independent
  human and CI gates.
  Verification: inspect the relevant owner guidance and
  walk through one parallel and one sequential bounded Work plan.
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
- **AC-5 TODO** The child Works are integrated and the comparison is captured
  before this parent is completed.
  Verification: check `master` status for
  each mapped child and inspect the comparison record.

This plan does not change policy or tooling. Promote lasting rules to their
owners through the child Works; reconcile consequential delivery-workflow
choices through the applicable WDR lifecycle without rewriting accepted
records.
