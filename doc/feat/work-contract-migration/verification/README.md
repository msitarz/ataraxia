# Verify integrated contract migration

## Purpose

Ensure the migrated contracts, guidance, and tooling agree without losing
requirements or retaining obsolete acceptance bookkeeping.

## Goals

- Account for every inventoried Work and current reading route.
- Assess preserved scope and cross-tree dependencies using the completed diffs.
- Confirm the surviving commands and checks work together.

## Non-Goals

- Execute migrated Works or repeat empirical trials.
- Add a permanent migration checker or duplicate every child's review and tests.

## Acceptance criteria

### **AC-1 TODO** Complete and consistent migration coverage

Every inventory entry has a reviewed disposition: converted active contract,
updated owner, retired infrastructure, or preserved historical input. This
migration's own contracts are consistent with the final rules. Current reading
routes, glossary meanings, parent maps, and dependencies agree; active Work
requirements remain accounted for against the baseline. Obsolete instructions
are absent from current guidance, allowing clearly identified history.

### **AC-2 TODO** Integrated command behavior verified

Documentation links, formatting, and Mermaid checks pass for affected artifacts.
Focused surviving tooling tests establish the final work-check/test-command
behavior, including automatic structural checking through doc-check; retired
target/marker references no longer appear as live interfaces.
Review reuses applicable child evidence and reports outstanding failures or
unrun checks honestly. Full latest-reviewed-head CI remains the merge gate.

## Dependencies

- **TODO** [Active contract migration](../contracts/README.md): supplies all
  five reviewed rewrite groups.
- [Work contract template](../../../work-contract-template.md),
  [Work acceptance](../../../acceptance-tracing.md), and
  [WDRs 23–27](../../../wdr/README.md): supply the delivered authoring/evidence
  rules and lasting decisions.
- **TODO** [Tooling simplification](../tooling/README.md): supplies retained
  command behavior and focused execution evidence.
- **TODO** [Structural Work checking](../work-check/README.md): supplies the
  parser selection, explicit discovery convention, and integrated work-check
  behavior after contract migration.

## Links

- [Migration inventory](../inventory.md): baseline coverage and preservation
  scope.
