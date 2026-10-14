# Managed evaluation sandboxes

Preserve the approved direction for project-scoped temporary sandboxes: trusted
online workspace preparation, enforced native Codex execution, retained output
and session-scoped measurements. This is a new planning parent with direct
leaves, established independently of the historical shallow-clone tree.
It changes no executable behavior or current linked-worktree policy.

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

Before this ownership correction at `0a83600a6be11daa369ddbfd2ca3d421fae75e1c`,
managed preparation/runtime planning already existed while import and
communication remained in the shallow-clone tree. The correction moves their
owners without delivering commands.

```mermaid
flowchart LR
    B[Before: managed preparation/runtime, shallow-tree import/communication]
    B --> G[Delivered reconciliation: owners and Work-owned inputs]
    subgraph Proposed[Proposed: project managed root]
        W[Child-readable workspace: clone, tools, scratch]
        P[Private control: auth, Codex state, raw sessions, reviewer outputs]
        C[Create and list/remove] --> W
        E[Enforcement and readiness] --> X[Native sandbox-exec]
        X --> W
        X --> P
        X --> A[Accepted artifact import]
        Q[Executor communication Investigation] --> X
        P --> R[Conditional session report]
    end
    G --> C
    G --> E
    G --> I[Statistics-tool Investigation]
    I --> R
```

## Shared root and ownership

The default child location is `<system temp>/<project name>/sandboxes/<NAME>`.
Resolve system temp with `tempfile.gettempdir()` using its native
TMPDIR/TEMP/TMP and platform-default selection, and read the project name from
`pyproject.toml` `[project].name`; do not hardcode a macOS path or project name.
An optional `SANDBOX_ROOT` Make argument overrides the managed root. Create,
list, remove and exec share one authoritative resolution, ownership validation,
and per-name coordination object
([claim contract](lifecycle/active-state-exclusion/README.md)). Reject unsafe
resolved roots, including an unsuitable current-directory fallback, unsafe
project-name path components and invalid overrides, under the existing
containment, symlink, collision, ownership and permission safeguards.

Discover children locally, with per-child ownership metadata and no global
registry. Each ownership record includes an opaque unique generation ID and
the native identity of its created child directory. Bind repository ownership
to the canonical Git common directory: linked worktrees agree, while independent
checkouts sharing a project name cannot manage each other's children. A
conflicting owner blocks creation, removal and execution rather than
reassigning an existing child.
Keep a stable root-private per-name lock object across successful removal and
same-name recreation. It is coordination state rather than an ownership record
or registry, and direct-child listing ignores it.
The private control side remains inaccessible
to child commands even if physically beneath that root. A prepared workspace
does not itself enforce isolation. Source/history and command-network denial
remain distinct from the host transport needed to call the model service.

## Children and gates

- **DONE** Preparation and ownership reconciliation: preserved manual input,
  moved import and communication into direct children and superseded the empty
  implementation Work without completing its undelivered outcomes.
- **DONE** Delivered managed sandbox creation: online independent shallow
  clone, native setup/hooks/readiness, and retained failed state.
- **TODO** [Discover and safely remove sandboxes](lifecycle/README.md):
  trustworthy local discovery and preservation-aware removal; after creation.
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

The maintainer-authorized #315 correction assigns existing artifact import and
executor communication directly to this parent. Creation supersedes manual clone
preparation; enforcement/execution supersede the old runtime. The residual
shallow-clone tree was abandoned at maintainer request. Its registry selector
cleanup is recorded as complete in the historical
[shallow-clone parent map](https://github.com/msitarz/ataraxia/blob/ea784d4dbf02a87486842a2012ca9da852b94379/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/README.md#implementation-follow-up).
Do not run concurrent duplicate runtime implementations. Each leaf is one
coherent review outcome;
reassess its complete expected and actual diff against the
[five-minute review target](../../workflow.md#scope-and-sizing), splitting
before execution/publication when required.

No implementation, sandbox probes, model runs, statistics adoption, host-auth
reads, trial authorization or default-policy adoption is included here. Runtime
validation needs separately approved frozen conditions and model/effort/budget;
existing import, publication, independent review and latest-head CI gates
remain. Consequential policy changes follow the
[WDR route](../../wdr-workflow.md).

## Acceptance

- **AC-1 TODO** The reviewed child outcomes compose from owned preparation to
  enforced execution, retained output and accepted Work-branch import, with
  trustworthy supported reports or an explicit independently reviewed
  unsupported/no-fit reporting disposition, without duplicate owners or changes
  to ordinary Work delivery.

  Validation: independent integration review of child evidence and owner links,
  including consistent root/owner resolution, failed preparation, denied launch,
  exact resume, retained work, accepted tip/base and import boundaries; reuse
  leaf evidence rather than repeat probes or model runs. A no-fit finding does
  not fake report implementation or automatic adoption; follow reviewed Work
  lifecycle disposition for any unsatisfied integration outcome.
- **AC-2 TODO** On real command delivery, lasting usage and supported-condition
  limits are promoted from Work-owned inputs to one focused owner, discoverable
  from Make help, documentation, orchestrator and evaluation routes; measurement
  limits remain explicit.

  Validation: independently walk those routes and verify promotion before Work
  cleanup. CONTRIBUTING routes existing tool discovery and gains no sandbox
  procedure section; recommendations and estimates do not become policy.
