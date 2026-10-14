# Reviewed cleanup disposition

After [execution recovery](../execution-recovery/README.md), deliver one
host recording and validation interface for current explicit cleanup authority.
[Removal](../../removal/README.md) consumes it and owns deletion;
[native execution](../../../execution/README.md) consumes attempt invalidation.
Reuse the existing private marker and validated lock/update APIs. Creation
remains independent of Evaluation binding; failed preparation can receive a
validated host-side Work/orchestrator binding under the lock before disposition
and cleanup.

## Host authority and preservation bindings

The shared host recording interface accepts the owning orchestrator, current
identity/inventory bindings, retained destinations, review reference and
explicit retain/discard decisions; it returns a validated persisted disposition
or refuses without approval. Implementation may use a small shared helper and
existing Make routing; no new controller or external review service is required.

The owning orchestrator explicitly records cleanup disposition only after
artifacts are preserved and the maintainer has reviewed the cleanup decision.
It identifies that owner and review, the generation, current run/attempt and
session identity when known, exact workspace state (tip and changes), and exact
private output/artifact inventory or revisions, with retained destinations and
accepted import evidence or reviewed discard decisions where applicable.
Inactivity, clean status, a session ending, or executor-written claims cannot
supply this approval. Disposition is private host authority, not delegated to
the executor. Its host recording operation validates ownership and current
bindings under the same exclusive lock; it cannot race launch or deletion.
Do not require a new review system: reuse existing Work/PR review and artifact
preservation evidence. Removal consumes the validated disposition.

The [execution protocol](../execution-recovery/README.md#binding-and-attempts)
owns safe invalidation before identified launch/resume attempts, including
failed/rejected requests. Any changed run, workspace, preparation state or
output invalidates the binding; missing/inconsistent bindings always refuse
removal. Failed preparation also requires explicit reviewed disposition covering
its partial workspace and diagnostics; no absence-of-work bypass is allowed.
The recording API and read validation require exact current generation,
attempt/session when known, workspace tip/changes, preparation state and private
output inventory/revisions. Changed bindings make a previously persisted
record unusable even if no writer cleared it. Exercise invalidation through the
execution child's API, so initial/resumed/failed/rejected attempt handling has
one owner. Host recording validates source Work binding through that same
protocol; it never accepts executor claims as host authority.

Failed preparation with no run/session has explicit absent execution provenance
and still needs disposition covering partial workspace and diagnostics. Unknown
execution cannot be approved for removal by disposition recording; only the
execution owner's safe recovery can establish stoppage and preserve results.
Removal verifies retained destinations/evidence immediately before deletion;
this child supplies the reusable current-binding validation under exclusion.

## Acceptance

- **AC-1 TODO** Only the owning orchestrator can record a current explicit
  cleanup disposition after preservation and maintainer review. Inactivity,
  clean status, a session ending or executor-written claims cannot supply
  approval. Host authority binds review and exact retained/discarded material;
  recording holds the same exclusive lock and cannot race launch or deletion.

  Validation: criterion-marked host-record fixtures exercise missing review,
  wrong owner, missing/invalid source Work binding, missing preservation or
  review/import evidence, retained destinations and explicit discard decisions.
  Independently review existing evidence bindings and child/private trust
  boundary; test lock contention with shared launch/deletion fixtures. No model
  run or speculative controller is required for this shared safety outcome.
- **AC-2 TODO** New, resumed, failed or rejected execution and changed output
  cannot reuse stale approval; failed preparation and unknown execution receive
  no automatic exemption. Missing/inconsistent generation, run/session,
  workspace, preparation or inventory bindings refuse approval/removal.

  Validation: criterion-marked host-record fixtures exercise generation/run/
  session/output/workspace/preparation mismatch, changed artifacts,
  rejected/failed/resumed launch using the shared attempt API, failed
  preparation with partial or absent workspace, and unknown execution
  before/after safe recovery. Assert refusal preserves protected bytes and
  supplies no approval; removal verifies its own destructive command
  integration.
