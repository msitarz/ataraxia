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

A supported pinned runtime enforces only the declared child access.

- Allowed access covers workspace, necessary tool/runtime and interpreter/hook
  reads, clone-local scratch and Git writes.
- Auth, private Codex state, raw sessions, reviewer outputs, source/sibling
  repositories/history and undeclared host locations remain inaccessible,
  including private control beneath the managed root.
- Command-network denial remains independent of host model-service transport.
- Effective profile/configuration uses matched non-secret allowed/denied
  controls with explicit platform limits, while unsupported
  runtime/configuration/tool grants fail closed.
- Absent origin/offline flags and historical
  [boundary](../preparation-input.md#boundary-and-handoff-input) or
  [isolation](../isolation-input.md) inputs establish no current
  denial/readiness.

### **AC-2 TODO** Bind start and resume to current readiness

Initial start and exact UUID resume require current bound readiness.

- Start binds workspace and immutable original base, while resume rechecks that
  base, accepted checkpoint HEAD, UUID and boundary without admitting unreviewed
  HEAD/UUID changes.
- Both inspect prepared tools/hooks and privacy before execution, allowing
  reviewed committed executor checkpoints.
- Launcher TMPDIR remains unchanged for Codex `:tmpdir`, while child
  TMPDIR/TMPPREFIX and scratch stay workspace-local regardless of managed-root
  selection.
- Exposure, stale readiness, missing tools/hooks, install attempts, invalid
  controls or changed configuration stops with retained diagnostics and no extra
  grants.
- New probe conditions require freezing and applicable approval before
  execution, while historical deterministic checks support only their tested
  condition.

Model start/resume belongs to [native execution](../execution/README.md).

## Dependencies

- **DONE** [Managed sandbox creation](../../../evaluation-sandboxes.md):
  supplies the prepared workspace and existing root/ownership machinery.
