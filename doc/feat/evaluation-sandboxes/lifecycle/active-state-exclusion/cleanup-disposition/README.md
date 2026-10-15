# Reviewed cleanup disposition

## Purpose

Make sandbox cleanup authority depend on current preserved material and explicit
maintainer-reviewed host disposition.

## Goals

- Record host-controlled cleanup decisions under shared exclusion.
- Bind authority to exact current identity, workspace and private output.
- Refuse stale approval and unknown execution without exemptions for failed
  preparation.

## Mechanisms

- The existing private lifecycle marker stores host cleanup authority alongside
  the preserved identity and attempt state it binds.
- Shared exclusive acquisition and validated updates serialize disposition
  recording with launch and deletion.
- Existing Work/PR review evidence supplies review and preservation provenance
  without a new controller or external review service.

## Acceptance criteria

### **AC-1 TODO** Record only reviewed host cleanup authority

Only the owning orchestrator can record current cleanup authority after
preservation and maintainer review.

- Recording accepts current identity/inventory, retained destinations, review
  reference and explicit retain/discard decisions, returning validated persisted
  authority under the same exclusive lock as launch/deletion.
- Persisted disposition identifies owner/review, generation, current run/attempt
  and known session, exact workspace tip/changes, preparation state and private
  output/artifact inventory or revisions.
- Retained destinations and accepted import evidence or reviewed discard
  decisions cover the applicable material.
- Missing review, wrong owner, invalid/missing source Work binding or missing
  preservation/review/import evidence returns refusal without approval.
- Source Work validation uses the execution protocol, and private host authority
  never derives from executor claims, inactivity, clean status or a session
  ending.

[Removal](../../removal/README.md) consumes this current-binding validation and
verifies retained destinations/evidence before deletion; a small shared helper
and existing Make routing suffice without a new review system.

### **AC-2 TODO** Reject stale or incomplete disposition

Stale or incomplete disposition refuses cleanup without changing protected
bytes.

- The [attempt protocol](../execution-recovery/README.md#binding-and-attempts)
  invalidates approval before identified initial/resumed/failed/rejected launch
  attempts.
- Missing, inconsistent or changed generation, attempt/session, workspace,
  preparation or output/inventory bindings invalidate approval even without an
  explicit clear, including changed artifact bytes/revisions.
- Failed preparation may receive validated source Work/owner binding under the
  lock, but still requires reviewed disposition for partial material and
  diagnostics despite absent workspace or run/session provenance.
- Unknown execution cannot receive removal approval before the execution owner's
  safe recovery establishes stoppage and preservation.

Creation remains independent of Evaluation binding, and refusal grants no
approval.

## Dependencies

- **TODO** [Execution attempts and recovery](../execution-recovery/README.md):
  supplies source binding, current attempt identity, invalidation and safe
  recovery.
- **TODO** [Stable lock and durable marker](../lock-and-marker/README.md):
  supplies the validated private record and exclusive update scope.
