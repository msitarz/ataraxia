# Apply reuse when defining a Work

Clarify [Work contract guidance](../../../../../../workflow.md) so a definer
inspects current machinery, identifies requirements it already fulfills, and
defines the remaining required gap before proposing new machinery.

Implement this in the existing contract-definition prose. Link to the
[repair and scope owner](../../../../../../change-rules.md#fix-the-underlying-problem)
for the underlying principle rather than restating its full policy. Reuse
suitable existing commands, APIs, helpers, and evidence; introduce machinery
when the existing path cannot fulfill the required outcome and explain that
limitation. Existing behavior remains evidence to assess against the required
outcome, rather than automatically becoming the intended contract.

Scope is this guidance clarification in `doc/workflow.md` and ordinary Work
completion updates. No mandatory inventory, checklist, report, new owner, or
unconditional reuse of mismatched abstractions. Preserve existing contract,
acceptance, sizing, lifecycle, and review requirements. This leaf has no child
Works and does not implement or rewrite Mermaid validation contracts.

## Acceptance

- **AC-1 DONE** When defining a Work, the guidance explicitly calls for
  inspecting current machinery, distinguishing already-fulfilled requirements
  from the remaining required gap, and defining scope from that gap.
  Validation: independently inspect the changed owner section and walk through
  a requirement already fulfilled by an existing command; confirm the guidance
  leads to no duplicate machinery for that requirement.
- **AC-2 DONE** The guidance calls for suitable reuse of existing commands,
  APIs, helpers, and evidence, and explains the limitation when existing
  machinery cannot fulfill a required outcome.
  Validation: independently walk through a genuine missing capability and a
  mismatched abstraction; confirm the guidance permits the necessary addition
  without requiring inappropriate reuse.
- **AC-3 DONE** The clarification links to the existing repair owner, introduces
  no mandatory planning artifact or owner, and preserves substantive Work
  requirements and the review-effort target.
  Validation: independently review the whole affected section and related
  sizing guidance, compare the diff, and run `make doc-check` plus
  `make ac-check` for this README.
