# Agent responsibilities and model routing

Separate Work contract definition from bounded implementation while retaining
the orchestrator's overall scope, independent review, and delivery gates. The
maintainer selects GPT-6.1 Sol at medium effort for the definer and GPT-6 Luna
at medium effort for executor, cleaner, and publisher responsibilities.

## Delivery map

- **TODO** [Role policy adoption](policy/README.md): reconcile role boundaries,
  model routing, concise handoffs, and the workflow decision at their owners.

Merge this plan before adoption. Adoption follows the delivered
[cleanup procedure](../../branch-cleanup.md) and
[cleaner route](../../orchestrator.md#roles-and-delegation), plus the
[publisher guidance](../publication-tool-guidance/publisher/README.md). Those
owners retain their procedural responsibilities. Serialize shared orchestrator
guidance, glossary, WDR index, and parent-map edits.
This plan changes no current policy.

- **AC-1 TODO** Given the adoption contract and prerequisite guidance Works,
  their boundaries and sequence define one reviewable policy outcome without
  duplicating operational procedures or weakening independent review.

  Validation: manually review ownership, dependencies, and expected adoption
  scope against current orchestration, Work, PR, cleanup, and WDR guidance.
