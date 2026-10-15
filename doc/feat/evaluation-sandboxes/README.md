# Managed evaluation sandboxes

## Purpose

Provide project-scoped temporary workspaces whose preparation, restricted
execution, retained output and accepted import have one coherent ownership
contract.

## Goals

- Compose delivered creation with native runtime readiness and execution.
- Share safe root, ownership and lifecycle rules across sandbox commands.
- Retain attributable output for accepted Work-branch delivery.
- Provide supported session reports or an explicit reviewed no-fit disposition.
- Promote lasting command usage and supported-condition limits to their owner.

## Non-Goals

- Authorize sandbox probes, model runs, host-auth reads or statistics adoption.
- Change ordinary linked-worktree or Work delivery policy.
- Adopt a default sandbox or statistics policy from a recommendation.
- Run duplicate implementations of the retired runtime contracts.

## Mechanisms

`script/sandbox.py` and the Make interface deliver managed creation;
[usage guidance](../../evaluation-sandboxes.md) owns its current interface and
limits. The remaining children extend that machinery using native Codex
controls rather than a new sandbox framework or controller service.

### Shared root and ownership

#### Root selection

- Creation, listing, removal and execution share one root resolver and ownership
  validator.
- The default child path is `<system temp>/<project name>/sandboxes/<NAME>`.
- `tempfile.gettempdir()` selects system temp through native TMPDIR/TEMP/TMP and
  platform defaults, without a hardcoded macOS path.
- The project name comes from `pyproject.toml` `[project].name`, without a
  hardcoded name.
- Optional `SANDBOX_ROOT` overrides the managed root through the Make interface.
- Unsafe resolved roots, including unsuitable current-directory fallbacks,
  unsafe project-name components and invalid overrides, are rejected under
  existing containment, symlink, collision, ownership and permission safeguards.

#### Ownership and private control

- Local per-child metadata needs no registry and binds repository ownership to
  the canonical Git common directory, so linked worktrees agree and independent
  checkouts cannot manage one another's children.
- Conflicting ownership blocks creation, removal and execution without
  reassigning the child.
- The [active-state owner](lifecycle/active-state-exclusion/README.md) extends
  the existing record into an uncommitted lifecycle marker with opaque unique
  generation and native directory identity, and owns execution provenance and
  reviewed cleanup disposition.
- Creation, execution and removal automatically share its stable root-private
  per-name OS lock, retained across removal/recreation as coordination state and
  ignored by direct-child listing.
- Listing observes existing locks without creating or changing them.
- Unsupported records are safely rejected, and no existing sandboxes need
  migration.
- Private control remains inaccessible to child commands even beneath the
  managed root.
- Preparation enforces no isolation, and source/history and command-network
  denial remain separate from host model-service transport.

## Visuals

At verified revision `44f40de`, creation prepares an independent shallow clone,
performs native setup/readiness and retains failed preparation state. Runtime,
lifecycle locks, discovery, removal, import and reporting below are proposed:

```mermaid
flowchart LR
    C[Delivered: sandbox-create] --> W[Child workspace: clone, tools, scratch]
    C --> P[Private preparation record]
    P --> L[Proposed: lifecycle marker and stable lock]
    L --> D[Proposed: read-only discovery and guarded removal]
    L --> X[Proposed: native execution and retained artifacts]
    E[Proposed: enforced readiness] --> X
    Q[Communication findings] --> X
    X --> A[Proposed: accepted Work-branch import]
    X --> R[Conditional private session report]
    S[Statistics findings] --> R
```

The private side contains auth, Codex state, raw sessions and reviewer outputs;
child commands cannot read it. Statistics may conclude that no method fits.

## Acceptance criteria

### **AC-1 TODO** Compose owned sandbox delivery

Reviewed children compose safe preparation, enforced execution, retained output
and accepted Work-branch import.

- Commands agree on shared root/ownership and preserve their child-owned
  failure, resume and import boundaries.
- Reporting delivers trustworthy supported measurements or an independently
  reviewed unsupported/no-fit disposition without claiming implementation or
  adoption.
- Unsatisfied integration outcomes receive a reviewed
  [lifecycle disposition](../../workflow.md#lifecycle), while ordinary delivery
  and independent review retain
  [their owners](../../orchestrator.md#review-and-return).

### **AC-2 TODO** Publish discoverable command usage and limits

Delivered command usage and supported-condition limits reach one
[focused owner](../../evaluation-sandboxes.md) before Work cleanup.

- Make help, documentation, orchestrator and evaluation routes discover that
  owner as real commands deliver.
- Measurement limits stay explicit, and recommendations/estimates do not become
  policy.
- CONTRIBUTING retains tool-discovery routing without a sandbox procedure
  section.

## Children

- **DONE** Preparation and ownership reconciliation: preserved manual input,
  moved import and communication into direct children and superseded the empty
  implementation Work without completing its undelivered outcomes.
- **DONE** Delivered managed sandbox creation: online independent shallow
  clone, native setup/hooks/readiness, and retained failed state.
- **TODO** [Discover and safely remove sandboxes](lifecycle/README.md):
  shared lifecycle safety with creation integration, then read-only discovery
  and removal after explicit reviewed disposition.
- **TODO** [Enforced runtime readiness](enforcement/README.md): reuse native
  boundary controls, private state separation and effective start/resume gates;
  after creation.
- **TODO** [Native execution and retained artifacts](execution/README.md):
  `sandbox-exec` initial/exact-session resume and failure preservation; after
  enforcement and lifecycle active-state guards.
- **TODO**
  [Executor communication Investigation](executor-communication/README.md):
  investigate native exec/resume behavior, routing, failure/recovery and whether
  app-server control is needed; findings inform native execution without owning
  its implementation.
- **TODO** [Accepted executor commit import](artifact-import/README.md):
  accepted output into a designated full-history Work branch after reviewed
  execution.
- **TODO** [Session statistics Investigation](statistics/README.md): compare
  tokenuse, suitable Python alternatives and native CLI data; independent of
  model execution.
- **TODO** [Conditional report integration](reporting/README.md): only after
  reviewed statistics findings, integrate a fitting method using declared data
  or record an explicit reviewed unsupported/no-fit disposition; no tool
  adoption is predetermined.

## Additional context

Historical planning baseline: `master` at
`21d22e7847842d41aa34800593b6b193129c55f8` (#314) has manual clone-preparation,
runtime and import contracts, existing `worktree-create` and native Make setup,
but no managed sandbox targets. Frozen
[#315](https://github.com/msitarz/ataraxia/pull/315) at
`a8fd90ccb62f9593df499082e19a1a8c17eddb13` is frozen comparison input.
Historical integration base was merged #316 at
`a1a9c1dbbc5be6ccfad7a2914be4f0feb6255b67`. The maintainer approved reconciling
PR #315 onto it, retaining useful manual inputs at the
[Work-owned inputs](preparation-input.md). Those inputs preserve immutable
provenance. The additional [isolation findings](isolation-input.md) retain the
bounded standalone model result and separate project setup evidence from the
retired shallow-clone tree. Preparation evidence supports only the tested Darwin
Intel deterministic condition; it establishes neither filtered-answer exclusion
nor model-session isolation, and did not capture the full effective environment.

Before ownership reconciliation at `0a83600a6be11daa369ddbfd2ca3d421fae75e1c`,
managed preparation/runtime planning existed while import and communication
remained in the shallow-clone tree. The delivered reconciliation moved their
owners and retained Work-owned inputs; later creation delivery supplied the
managed command. Claims in the preparation input that no managed commands exist
refer to its historical baseline.

The maintainer-authorized #315 correction assigned artifact import and executor
communication directly here. Creation supersedes manual clone preparation;
enforcement/execution supersede the old runtime. The residual shallow-clone
tree was abandoned at maintainer request, with selector cleanup retained in its
[historical map](https://github.com/msitarz/ataraxia/blob/ea784d4dbf02a87486842a2012ca9da852b94379/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/README.md#implementation-follow-up).

Runtime evidence requires separately approved frozen conditions and
model/effort/budget. [Empirical evaluation](../../evaluation.md) owns execution
conditions; [Work sizing](../../workflow.md#scope-and-sizing) owns expected and
actual review scope, and [publication](../../pull-requests.md#publishing) and
[latest-head CI](../../validation.md) retain their independent/maintainer gates.
Consequential policy changes follow the [WDR route](../../wdr-workflow.md).
