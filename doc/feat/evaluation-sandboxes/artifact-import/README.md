# Accepted executor commit import

## Purpose

Deliver independently accepted executor commits to the designated full-history
Work branch without expanding executor access.

## Goals

- Import only accepted identities through an explicit assigned ref.
- Preserve work and delivery commit boundaries during reconciliation.
- Hand reviewed latest-head output to the existing publication owner.

## Mechanisms

- Explicit Git fetch imports an assigned accepted ref into a full-history
  receiver.
- Git rebase reconciles accepted commits onto the designated Work branch.
- Expected Work HEAD supplies the compare-and-swap guard on branch updates.

## Acceptance criteria

### **AC-1 TODO** Import the exact accepted ref into a guarded receiver

Orchestrator-controlled import requires the exact accepted executor tip/base and
expected Work HEAD after independent acceptance and final correction. It fetches
only the explicit assigned ref into a nonshallow receiver with full history and
rejects stale acceptance, missing ancestry, unrelated/unexpected refs and failed
compare-and-swap guards without publication.

### **AC-2 TODO** Preserve work through unchanged or advanced bases

Unchanged-base import preserves commit identity. Advanced-base rebase preserves
authors/author metadata, commit subjects/order, exact binary bytes, modes,
rename/delete changes and implementation/evidence-before-cleanup boundaries,
including the upstream content of a clean advanced base. Conflict halts
publication until reviewer-owned resolution and refreshed evidence accepted for
the rewritten latest head. Executor state/auth, permissions and source input
remain untouched; host production operations retain signing settings and normal
hooks.

### **AC-3 TODO** Hand off only reviewed latest-head output

Only reviewed latest Work-branch output reaches orchestrator-controlled
[publication](../../../pull-requests.md#publishing), subject to
[latest-head CI](../../../validation.md) and maintainer review. Master is never
a delivery target or rewritten; source is unchanged and executor permissions
gain no publication access. Live GitHub PR/CI experiments, alternate patch
transport and default-policy adoption remain outside scope.

## Dependencies

- **TODO** [Native execution and retained artifacts](../execution/README.md):
  supplies exact independently accepted runtime output after final correction.

## Links

- [Historical delivery input](delivery-protocol.md): bounded fixture
  observations supply context without completing this Work or authorizing
  adoption.
- [Runtime enforcement](../enforcement/README.md) and
  [historical isolation input](../isolation-input.md): own the runtime boundary
  and its separate prior observations.
