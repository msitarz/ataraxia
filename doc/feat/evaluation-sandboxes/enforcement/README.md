# Enforced runtime readiness

Under the [reconciled ownership](../README.md#children-and-gates), after
[creation](../creation/README.md) supplies a prepared workspace, reuse
existing native Codex boundary controls. Own effective enforcement and readiness
shared by initial start and exact UUID resume; the execution leaf consumes this
gate. No new sandbox system or general platform framework is planned.

Use the
[preserved boundary/handoff input](../../../evaluation-sandboxes.md#boundary-and-handoff-input)
without treating historical controls as current readiness.

## Acceptance

- **AC-1 TODO** A supported pinned runtime admits only the declared child
  workspace, necessary tools/runtime reads, clone-local scratch and Git writes.
  Auth, private Codex state, raw sessions, reviewer outputs, source/sibling
  repositories/history and undeclared host locations remain inaccessible to
  child commands. Command network is denied independently of host model
  transport. Unsupported runtime, configuration or tool grants fail closed.

  Validation: criterion-marked effective-profile/configuration tests use the
  native controls and smallest non-secret matched allowed/denied cases at our
  boundary. Independent review verifies effective context, private separation
  even beneath the managed root, permitted interpreter/hook reads and platform
  limits; absent origin/offline flags do not establish denial.
- **AC-2 TODO** Initial start binds the workspace and immutable original base;
  resume rechecks that base plus accepted checkpoint HEAD, exact UUID and the
  same boundary, permitting reviewed executor commits after preparation.
  Both recheck prepared tools/hooks and privacy inspection before execution.
  Launcher TMPDIR remains unchanged for the Codex `:tmpdir` host boundary;
  child TMPDIR/TMPPREFIX and scratch stay workspace-local. Managed-root
  resolution does not replace the launcher's temporary-directory setting.
  Exposure, stale readiness, missing tools/hooks, install attempts,
  invalid controls or changed configuration stop with retained diagnostics and
  no extra grants.

  Validation: criterion-marked readiness tests cover stale bindings and failure
  preservation, accepted committed checkpoint resume, rejection of unreviewed
  HEAD/UUID changes, and useful tool/hook/scratch controls under the effective
  profile. Freeze any newly needed probe condition and obtain applicable
  approval before execution; historical deterministic checks establish only
  their tested condition, and model start/resume belongs to the execution leaf.
