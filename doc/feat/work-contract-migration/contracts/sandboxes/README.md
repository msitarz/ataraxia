# Rewrite sandbox contracts

## Purpose

Make the managed sandbox contracts readable through the new template without
changing what their Works are authorized to deliver.

## Goals

- Give each criterion one coherent outcome and each contract a clear overview.
- Preserve local requirements, parent maps, and cross-Work dependencies.

## Non-Goals

- Implement the listed Works or resolve their pending decisions.
- Change historical evidence, approvals, or execution conditions.

## Acceptance criteria

### **AC-1 TODO** Readable contracts with preserved outcomes

Every scoped contract uses the template with focused outcomes and only useful
optional sections. Comparison with its pre-migration version accounts for all
required behavior, boundaries, and meaningful context. Substantive conditions
from Validation clauses become outcomes; generic execution instructions and
repetition are removed. Known uncertainty stays explicit rather than becoming
an invented contract or completion claim.

Preserve native isolation and supported-condition limits, shared identity/root
ownership, lock and generation safety, execution recovery, disposition, and
import/reporting boundaries. Listing is already converted. Historical
preparation/isolation/delivery inputs remain evidence, not new execution
authority.

### **AC-2 TODO** Consistent dependencies and ownership

Parent maps, linked supporting artifacts, and active criterion/anchor references
agree with the rewritten contracts. Dependencies explain what is consumed and
when, separately from immediate children. References to retired acceptance tools
are removed from current instructions without rewriting historical records.

## Dependencies

- **TODO** [Guidance alignment](../../guidance/README.md): supplies authoring
  rules.
- **TODO** [Tooling simplification](../../tooling/README.md): removes marker
  coupling and establishes the retained declaration-check surface.

## Links

- [Managed evaluation sandboxes](../../../../feat/evaluation-sandboxes/README.md).
- [Accepted executor commit import](../../../../feat/evaluation-sandboxes/artifact-import/README.md).
- [Enforced runtime readiness](../../../../feat/evaluation-sandboxes/enforcement/README.md).
- [Native execution and retained artifacts](../../../../feat/evaluation-sandboxes/execution/README.md).
- [Executor communication Investigation](../../../../feat/evaluation-sandboxes/executor-communication/README.md).
- [Sandbox lifecycle](../../../../feat/evaluation-sandboxes/lifecycle/README.md).
- [Per-sandbox active-state exclusion](../../../../feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md).
- [Reviewed cleanup disposition](../../../../feat/evaluation-sandboxes/lifecycle/active-state-exclusion/cleanup-disposition/README.md).
- [Execution attempts and recovery](../../../../feat/evaluation-sandboxes/lifecycle/active-state-exclusion/execution-recovery/README.md).
- [Stable lock and durable marker](../../../../feat/evaluation-sandboxes/lifecycle/active-state-exclusion/lock-and-marker/README.md).
- [Read-only sandbox discovery](../../../../feat/evaluation-sandboxes/lifecycle/listing/README.md).
- [Preservation-aware sandbox removal](../../../../feat/evaluation-sandboxes/lifecycle/removal/README.md).
- [Conditional session report integration](../../../../feat/evaluation-sandboxes/reporting/README.md).
- [Session statistics Investigation](../../../../feat/evaluation-sandboxes/statistics/README.md).
