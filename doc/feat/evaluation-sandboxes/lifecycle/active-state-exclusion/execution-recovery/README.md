# Execution attempts and recovery

After the
[delivered lifecycle foundation](../README.md#child-outcomes-and-dependencies),
deliver the shared execution-attempt and recovery protocol consumed by
[native execution](../../../execution/README.md). This child owns Work/session
binding, retained attempt state and process lifetime protection; native CLI
inputs, readiness/model gates, exec/resume routing and actual model runs remain
with that consumer. Use real shared APIs and small process fixtures here.

## Binding and attempts

Before initial execution, bind the owning Evaluation Work
repository path and owning orchestrator identity under the exclusive lock.
For each execution attempt record a unique run identity,
Codex session UUID when available, preparation/execution outcome (including
incomplete or unknown), and private output/artifact paths. A Codex session UUID
is distinct from a delegated agent identifier; add an agent identifier only if
needed for provenance. Never invent a missing UUID. Keep prior attempts and
artifacts when resuming or failing rather than overwrite their provenance.

Initial `sandbox-exec` requires `EVALUATION_WORK=repository/relative/path` and
host-controlled owning-orchestrator provenance. Validate a contained path with a
Work README in the owning source repository/Work branch; the Work need not exist
in the sandbox frozen clone. Missing, escaped or invalid bindings refuse launch.
Resume requires agreement with the recorded Work/orchestrator identity and exact
session UUID; it cannot reassign ownership. Creation keeps its delivered inputs
and does not require an Evaluation binding. Failed preparation may receive a
validated host-side Work/orchestrator binding under the lock before disposition
and cleanup. Execution records binding and run/outcome/artifact fields and
invalidation, never disposal approval. The later
[disposition child](../cleanup-disposition/README.md) owns host
review/preservation bindings. This child clears any disposition before an
identified attempted initial/resumed launch, including failed/rejected attempts;
trusted identity is required before updating, so unsafe requests preserve the
record and cannot confer approval. Later disposition recording consumes this
invalidation and current attempt identity rather than moving launch ownership.

## Protected process lifetime

`sandbox-exec` acquires automatically before launch and holds exclusion until
execution and all descendants capable of accessing the workspace/private output
are stopped and results retained. The orchestrator owns review and disposal,
not manual liveness unlocking. Implement OS lock lifetime and process handling
so a crashed wrapper cannot release exclusion while descendants still operate.
Do not let descendants escape the protected lifetime. If stopping or observing
all descendants cannot be established, retain an unknown execution marker and
refuse launch/removal until host-side recovery establishes stoppage and retains
results under the lock. OS release after process death alone does not establish
completed execution or disposability. No stale active bit needs manual clearing.

The shared attempt API accepts a locked sandbox, validated source Work/owner,
initial or exact-session resume identity and a process invocation; it persists
unique attempt/provenance before launch, retains outcomes/artifacts, and returns
completed/incomplete/unknown state. The recovery API accepts the same locked
identity and host-side stoppage/preservation evidence; it refuses while safety
cannot be established and retains prior results before permitting later action.
These are semantic interfaces, not fixed Python signatures. Keep mechanism and
supported OS limits explicit; do not add a controller or permit an escaped
child to operate after exclusion ends.

## Acceptance

- **AC-1 TODO** Initial execution accepts only a contained existing source Work
  README and host-controlled owning orchestrator binding; exact UUID resume
  agrees with recorded Work/owner/session and cannot reassign it. Each attempt
  has unique run identity, honest available UUID, outcome and private artifact
  paths; earlier attempts survive failure/resume. Identified failed/rejected
  attempts invalidate disposition, while unsafe identity refuses without update.

  Validation: criterion-marked shared-API host/process fixtures cover a Work
  absent from the frozen clone but present in the source Work branch,
  missing/escaped/invalid Work, resume ownership or UUID mismatch, no available
  UUID, successive attempts, failed/rejected launch and retained artifacts.
  Inspect private modes, provenance and unchanged unsafe records; native
  execution verifies command integration and authorization separately.
- **AC-2 TODO** Normal completion, interruption and crashes retain outcomes
  and artifacts; exclusion lasts through descendants and result retention.
  Unknown execution fails closed until safe recovery. OS release after death
  alone grants no completed outcome or disposability.

  Validation: criterion-marked process fixtures terminate wrappers with live
  descendants and verify exclusion or unknown-state refusal until stoppage and
  preservation; cover interrupted attempt updates and safe reacquisition.
  Review supported OS semantics, descendant lifetime and recovery, including
  rejected recovery and successful host recovery preserving earlier results.
  Test acquisition refusal for later execution/removal via the shared API;
  consumers verify their real command paths.
