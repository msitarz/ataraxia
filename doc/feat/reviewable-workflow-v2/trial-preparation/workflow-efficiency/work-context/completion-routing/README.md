# Completion routing

Route a small, applicable executor Definition of Done (DoD) from its existing
owner so it can be selected for a Work without copying policy into each
contract. The
[Work-context parent](../README.md#works) tracks this outcome. Coordinate
guidance-file edits with the
[handoffs](../../handoffs/README.md) and
[guidance-application](../../guidance-application/README.md) Works; do not
change their contracts or claim their outcomes.

## Acceptance

- **AC-1 TODO** One existing owner defines a concise executor-finish DoD route
  that applies only relevant rules to the selected Work and is generated or
  selected for that Work instead of duplicated in each Work contract.
  Verification: inspect the owning guidance and walk through two Works with
  different applicable completion requirements, confirming irrelevant rules
  are omitted.
- **AC-2 TODO** The route distinguishes executor completion from review and
  merge, and covers active acceptance markers, observed evidence, affected
  checks, retained `DONE` results before cleanup, and local return of the
  artifact and evidence.
  Verification: walk a sample executor completion through its active criteria,
  results, retained contract, and local return; confirm review and merge remain
  later gates.
- **AC-3 TODO** The final wording links existing authoritative guidance and
  coordinates changes with mapped neighboring Works without duplicating or
  superseding their contracts.
  Verification: inspect changed owner sections and follow links to the
  handoff, PR-evidence, and guidance-application contracts, checking each
  requirement still has one owner.
