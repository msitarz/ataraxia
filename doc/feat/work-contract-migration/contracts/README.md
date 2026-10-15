# Migrate active Work contracts

## Purpose

Make every existing Work readable through focused outcomes while retaining its
approved behavior, scope, dependencies, and unresolved decisions.

## Goals

- Convert all inventoried contracts to the template.
- Keep shared context in parents and local outcomes in the appropriate leaves.
- Preserve substantive requirements embedded in old Validation clauses.

## Non-Goals

- Execute any rewritten Work, approve a pending decision, or invent missing
  trial thresholds or product behavior.
- Rewrite historical evidence or add new Works merely to mirror AC headings.

## Acceptance criteria

### **AC-1 TODO** Every inventoried contract converted without scope drift

The five child groups cover every pre-migration Work README and its linked
supporting artifacts. Criteria state one coherent outcome each, collectively
covering purpose and goals. Existing outcomes, safety boundaries, statuses, and
prerequisites survive; routine checks and duplicated instructions are removed.
Already converted examples receive a consistency review rather than gratuitous
rewriting. Active ID/anchor references remain meaningful after splitting ACs.

### **AC-2 TODO** Parent and child contracts compose consistently

Parent maps preserve immediate-child ownership and lifecycle state. Dependencies
explain prerequisites separately from children; shared context is linked rather
than copied. Missing contracts or unresolved decisions remain explicit and owned
by their existing planning Work. Historical protocols and observed evidence are
not silently converted into current instructions or completed outcomes.

## Dependencies

- [Work contract template](../../../work-contract-template.md):
  supplies the delivered authoring rules.
- **DONE** The completed [tooling simplification outcome](../README.md#children)
  retired obsolete acceptance commands and test-marker coupling, so these
  rewrites are usable before work-check is integrated.

## Children

- **DONE** Workflow planning and trial contracts rewritten with preserved
  outcomes and ownership
  ([reviewable workflow](../../reviewable-workflow-v2/README.md)).
- **DONE** Managed sandbox contracts rewritten with preserved outcomes and
  ownership
  ([managed evaluation sandboxes](../../evaluation-sandboxes/README.md)).
- **TODO** [Package documentation contracts](package-readmes/README.md): migrate
  package README planning and documentation outcomes.
- **TODO** [Conditional complexity contracts](conditional-complexity/README.md):
  migrate investigation, adoption, and shared-owner dependencies.
- **TODO** [Standalone guidance and investigation](standalone/README.md): review
  validated-core and migrate the algebraic-data-type Investigation.

## Links

- [Inventory](../inventory.md): exact group membership and supporting artifacts.

## Additional context

Each group reads its parent overview before rewriting its leaves. Shared-owner
changes are coordinated by the migration owner at their authoritative guidance
owners. Cross-group dependency wording is
coordinated serially, especially validated-core and complexity adoption. This
migration does not relax review sizing or authorize the rewritten Works'
implementation.
