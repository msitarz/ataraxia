# Preservation-aware sandbox removal

## Purpose

Remove a managed sandbox only after its exact retained work and output have a
current reviewed cleanup disposition.

## Goals

- Expose guarded named sandbox removal under shared exclusion.
- Preserve all protected material on refusal or incomplete cleanup.
- Allow safe retry and fresh same-name creation after successful cleanup.

## Mechanisms

- `make sandbox-remove` exposes named deletion through existing Make routing.
- Shared lifecycle APIs supply root/owner resolution, exclusive scope, current
  disposition validation and execution-recovery guards.

## Acceptance criteria

### **AC-1 TODO** Remove only an owned safely stopped sandbox

`make sandbox-remove NAME=... [SANDBOX_ROOT=/absolute/path]` removes only the
named direct owned child and its explicitly owned private artifacts using the
shared
[root and ownership contract](../../README.md#shared-root-and-ownership).
It captures generation before waiting, acquires the stable exclusive OS lock,
and revalidates generation and native destination identity before final checks.
It holds exclusion through deletion so launch cannot race a check/delete gap.

Only supported metadata, verified stopped execution and current reviewed
orchestrator disposition admit deletion. Unsafe root/source, foreign ownership,
symlinks, escapes, malformed metadata, stale generation, busy lock and unknown
or potentially live descendants refuse cleanup. No force option bypasses these
guards. Deletion never follows symlinks or recursively traverses another owned
sandbox/private tree by artifact path.

### **AC-2 TODO** Cover exact protected material before deletion

Current disposition follows artifact preservation and maintainer review and
covers exact workspace state, meaningful commits, dirty/staged/untracked content
and private output through preserved exact artifacts or explicit reviewed
discard decisions. Retained destinations and evidence are verified before
destructive action. Clean status and inactivity alone are insufficient.

Wrong owner, missing retention and changed/absent run, workspace, output or
other bindings refuse deletion and invalidate approval. Failed preparation
requires the same review covering partial workspace and diagnostics; an absent
partial directory does not authorize deleting its marker or output. Every
refusal leaves workspace, private output and diagnostics unchanged.

### **AC-3 TODO** Retain recovery authority through incomplete cleanup

Successful deletion removes the generation marker last, retains stable lock
identity and permits a fresh same-name generation. Artifacts outside the
explicit cleanup set remain intact.

Partial failure or interruption during workspace/private deletion or marker
removal retains the marker and remaining material, records incomplete cleanup
when safe and blocks name reuse. Retry revalidates identity, current disposition
and retained evidence under the same lock before finishing; retained
reservations cannot be bypassed when partial directories are absent.

## Dependencies

- **TODO**
  [Per-sandbox active-state exclusion](../active-state-exclusion/README.md):
  supplies the shared identity, exclusion, disposition and recovery protocol
  completed before this Work integrates guarded deletion.
