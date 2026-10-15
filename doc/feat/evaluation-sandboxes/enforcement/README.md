# Enforced runtime readiness

## Purpose

Make prepared sandboxes usable for native execution only when their effective
boundary and readiness are established.

## Goals

- Restrict child access using supported pinned native Codex controls.
- Apply the same effective readiness gate to initial execution and exact-session
  resume.

## Mechanisms

- Native Codex boundary controls provide the effective restricted execution
  profile without a new sandbox system or general platform framework.
- Prepared tool/hook configuration supplies readiness inputs shared by initial
  invocation and exact-session resume.

## Acceptance criteria

### **AC-1 TODO** Enforce the declared child boundary

A supported pinned runtime admits only the declared child workspace, necessary
tool/runtime reads, clone-local scratch and Git writes. Auth, private Codex
state, raw sessions, reviewer outputs, source/sibling repositories and history,
and undeclared host locations remain inaccessible to child commands, including
when private control is physically beneath the managed root. Command network is
denied independently of host model-service transport. Unsupported runtime,
configuration or tool grants fail closed.

The effective profile/configuration establishes useful interpreter and hook
reads and matched non-secret allowed/denied controls at the native boundary.
Supported platform limits stay explicit; absent origin and offline flags do not
establish denial. Historical
[boundary input](../preparation-input.md#boundary-and-handoff-input) and
[isolation findings](../isolation-input.md) establish no current readiness.

### **AC-2 TODO** Bind start and resume to current readiness

Initial start binds workspace and immutable original base. Resume rechecks that
base, accepted checkpoint HEAD, exact UUID and the same boundary, permitting
reviewed committed executor checkpoints while rejecting unreviewed HEAD/UUID
changes. Both recheck prepared tools/hooks and privacy inspection before
execution.

Launcher TMPDIR stays unchanged for the Codex `:tmpdir` host boundary; child
TMPDIR/TMPPREFIX and scratch remain workspace-local. Managed-root selection does
not replace the launcher's temporary-directory setting. Exposure, stale
readiness, missing tools/hooks, install attempts, invalid controls and changed
configuration stop with retained diagnostics and no extra grants.

Any newly needed probe condition is frozen and receives applicable approval
before execution. Historical deterministic checks support only their tested
condition; model start/resume belongs to
[native execution](../execution/README.md).

## Dependencies

- **DONE** [Managed sandbox creation](../../../evaluation-sandboxes.md):
  supplies the prepared workspace and existing root/ownership machinery.
