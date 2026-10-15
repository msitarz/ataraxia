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

The host recording interface accepts the owning orchestrator, current
identity/inventory bindings, retained destinations, review reference and
explicit retain/discard decisions. Only that owner can record disposition after
artifact preservation and maintainer review. It returns validated persisted
authority or refuses without approval under the same exclusive lock as
launch/deletion. Implementation may use a small helper and existing Make
routing.

Disposition identifies owner/review, sandbox generation, current run/attempt and
session when known, exact workspace tip/changes and preparation state, and exact
private output/artifact inventory or revisions. Retained destinations and
accepted import evidence or explicit reviewed discard decisions cover the
material where applicable. Missing review, wrong owner, missing/invalid source
Work binding, missing preservation or review/import evidence refuses approval.
Source Work validation uses the execution protocol; executor claims never supply
host authority.

Inactivity, clean status and a session ending do not grant approval. Disposition
stays private and is never delegated to the executor.
[Removal](../../removal/README.md) consumes current-binding validation and
verifies retained destinations/evidence immediately before deletion; this Work
does not delete material.

### **AC-2 TODO** Reject stale or incomplete disposition

The [attempt protocol](../execution-recovery/README.md#binding-and-attempts)
invalidates disposition before identified initial, resumed, failed or rejected
launch attempts. Missing, inconsistent or changed generation, attempt/session,
workspace, preparation or output/inventory bindings make approval unusable even
if no writer cleared it. Changed artifact bytes/revisions cannot reuse approval.
Refusal preserves protected bytes and supplies no approval.

Failed preparation has no exemption: it can receive a validated source
Work/owner binding under the lock, but a partial or absent workspace and
explicitly absent run/session provenance still require disposition covering
partial material and diagnostics. Creation remains independent of Evaluation
binding. Unknown execution cannot be approved for removal; only safe recovery by
the execution owner can establish stoppage and preserve results first.

## Dependencies

- **TODO** [Execution attempts and recovery](../execution-recovery/README.md):
  supplies source binding, current attempt identity, invalidation and safe
  recovery.
- **TODO** [Stable lock and durable marker](../lock-and-marker/README.md):
  supplies the validated private record and exclusive update scope.
