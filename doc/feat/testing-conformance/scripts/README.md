# Script testing boundaries

Preserve registry, acceptance-tooling, and commit-hook contracts while applying
[testing guidance](../../../testing.md) at the smallest observable boundary.

## Delivery map

- **DONE** Registry boundaries: CLI relocation/selection, record contracts,
  payload contracts and script-owned shared arrangements now have precise
  fixtures, isolated unit/integration coverage and complete registry/Make
  consumer validation.
- **DONE** Acceptance tooling: typed command and declaration tests preserve
  scoped selection, neutral reports, exact diagnostics, and marker provenance.
- **DONE** Commit-message boundaries: migrated the checker, real Git-hook, and
  prepared-project prek cases into three strictly typed integration modules
  using shared isolated process/Git support. The 34 retained cases assert
  independent outputs, unchanged message and project inputs, and relevant Git
  state.

These are parent contracts, not implementation leaves. Merge this map, then
define each subtree's bounded leaves in separate planning PRs before execution.
Complete leaf diffs, including helper/fixture typing, must fit the
[five-minute review target](../../../workflow.md#scope-and-sizing); split before
expansion. Registry planning comes first; sequence shared support, conftest,
strict includes and parent-map edits. Acceptance command planning precedes
declarations; commit-message planning follows shared configuration edits.

Keep registry arrangements script-owned with narrow Make reuse. Each cleanup
leaf precisely annotates and explicitly includes its cleaned modules/helpers and
executable fixtures under normal strict Pyrefly. Extract cohesive fixture
ownership where necessary; no single leaf promises the entire legacy conftest
migration, broad types/casts/ignores or source precision reductions. Run
affected Make consumers when shared support changes. Preserve covers/full
criterion text and accurate partial claims when tests move, Given/When/Then and
independent literal expectations. Units start no processes; process/Git cases
are integration.

No production APIs, hook-launcher fixes, tool/configuration policy, measurements
or property-test adoption in this subtree. Discovered repairs become separate
Works. Follow [test ownership](../../../test-ownership.md) before removing
probes.

- **AC-1 DONE** Given completed script cleanup, retained tests observe registry,
  acceptance and commit-message contracts at their proper boundaries with
  independent complete expectations and preserved failures/state/provenance.

  Validation: independently review child outcomes, focused criterion execution,
  unit/integration placement, fixture ownership, strict checked-file inclusion,
  complete script-suite and affected Make-consumer execution, and latest-head
  CI.
