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

Orchestrator-controlled import accepts only the independently accepted final
executor tip/base.

- Final correction and expected Work HEAD precede fetching the explicit assigned
  ref into a nonshallow full-history receiver.
- Stale acceptance, missing ancestry, unrelated/unexpected refs and failed
  expected-HEAD compare-and-swap guards reject import without publication.

### **AC-2 TODO** Preserve work through unchanged or advanced bases

Import preserves accepted work and delivery boundaries at unchanged or advanced
bases.

- Unchanged-base import preserves commit identity.
- Advanced-base rebase preserves authors/author metadata, subjects/order, binary
  bytes, modes, rename/delete changes, upstream content and
  implementation/evidence-before-cleanup boundaries.
- Conflicts halt publication until reviewer-owned resolution and acceptance of
  refreshed latest-head evidence.
- Executor state/auth, permissions and source input remain untouched, while host
  production operations retain signing settings and normal hooks.

### **AC-3 TODO** Hand off only reviewed latest-head output

Only reviewed latest Work-branch output reaches
[orchestrator-controlled publication](../../../pull-requests.md#publishing).

- [Latest-head CI](../../../validation.md) and maintainer review remain
  required.
- Master is never a delivery target or rewritten, source stays unchanged and
  executor permissions gain no publication access.
- Live GitHub PR/CI experiments, alternate patch transport and default-policy
  adoption remain outside scope.

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
