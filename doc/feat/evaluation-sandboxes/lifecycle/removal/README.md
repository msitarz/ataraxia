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

`make sandbox-remove NAME=... [SANDBOX_ROOT=/absolute/path]` deletes only the
named direct owned child and its explicitly owned private artifacts.

- It uses [shared root/ownership](../../README.md#shared-root-and-ownership),
  captures generation before waiting and revalidates generation/native
  destination identity after acquiring the stable OS lock.
- Exclusion lasts through final checks and deletion, closing the
  launch/check/delete race.
- Supported metadata, stopped execution and current reviewed orchestrator
  disposition are required without a force bypass.
- Unsafe root/source, foreign ownership, symlinks, escapes, malformed metadata,
  stale generation, busy lock and unknown/potentially live descendants refuse
  cleanup.
- Deletion never follows symlinks or traverses another owned sandbox/private
  tree through artifact paths.

### **AC-2 TODO** Cover exact protected material before deletion

Deletion requires verified preservation or reviewed discard of all protected
material.

- Current maintainer-reviewed disposition covers exact workspace state,
  meaningful commits, dirty/staged/untracked content and private output.
- Retained destinations and evidence are verified before destructive action,
  while clean status/inactivity confer no authority.
- Wrong owner, missing retention or changed/absent run, workspace, output or
  other bindings invalidate approval and refuse deletion.
- Failed preparation requires the same review for partial workspace/diagnostics,
  and an absent directory never authorizes deleting its marker/output.
- Every refusal leaves workspace, private output and diagnostics unchanged.

### **AC-3 TODO** Retain recovery authority through incomplete cleanup

Cleanup either finishes safely or retains the reservation and material needed
for guarded retry.

- Success removes the generation marker last, retains stable lock identity and
  permits a fresh same-name generation without touching artifacts outside the
  cleanup set.
- Failure/interruption during workspace/private deletion or marker removal
  retains marker/material, records incomplete cleanup when safe and blocks name
  reuse even with absent partial directories.
- Retry revalidates identity, current disposition and retained evidence under
  the same lock before finishing.

## Dependencies

- **TODO**
  [Per-sandbox active-state exclusion](../active-state-exclusion/README.md):
  supplies the shared identity, exclusion, disposition and recovery protocol
  completed before this Work integrates guarded deletion.
