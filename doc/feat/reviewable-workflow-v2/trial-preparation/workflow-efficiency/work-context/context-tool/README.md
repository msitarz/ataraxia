# Work context tool

Provide a read-only Make tool that gathers bounded context for an orchestrator
or executor from an explicitly selected Work and applicable guidance. This
depends on [completion routing](../completion-routing/README.md), whose DoD the
tool presents from its owner. The
[Work-context parent](../README.md#works) maps the result. Coordinate shared
guidance-owner edits with
[guidance application](../../guidance-application/README.md),
[handoffs](../../handoffs/README.md), and
[PR evidence](../../pr-evidence/README.md); do not rewrite their contracts.

## Acceptance

- **AC-1 TODO** The Make-owned, read-only command accepts explicit role and
  Work selections, reports checkout path, branch, and revision, and presents
  the selected Work's local contract plus applicable guidance sections with
  source links and the filtered DoD.
  Verification: invoke the command for both roles on a sample Work and compare
  its output and source links with the checked-out contract and owner sections.
- **AC-2 TODO** Ambiguous task or guidance selection requires explicit
  selection; gathering is bounded and does not recursively load every link,
  ancestor, sibling, ADR, or glossary entry, and does not create a second
  policy manifest.
  Verification: exercise an ambiguous selection and inspect the resulting
  request for input; then use an explicit selection and verify excluded linked
  and neighboring material is absent.
- **AC-3 TODO** The tool does not mutate files or Git state and its selected
  guidance agrees with the existing owners and completion-routing contract.
  Verification: compare status and tracked-file hashes before and after both
  role invocations, then review source references against their owner text.
