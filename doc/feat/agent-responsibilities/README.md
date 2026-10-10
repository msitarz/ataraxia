# Agent responsibilities and model routing

Separate Work contract definition from bounded implementation while retaining
the orchestrator's overall scope, independent review, and delivery gates. The
maintainer selects GPT-6.1 Sol at medium effort for the definer and GPT-6 Luna
at medium effort for executor, cleaner, and publisher responsibilities.

## Delivery map

- **DONE** Role policy adoption: responsibility-based model routing and
  definition handoffs are defined in
  [orchestrator guidance](../../orchestrator.md#roles-and-delegation), with
  rationale in WDR 20 and operational procedures at their existing owners.

Merge this plan before adoption. Adoption follows the delivered
[cleanup procedure](../../branch-cleanup.md) and
[cleaner route](../../orchestrator.md#roles-and-delegation), plus the
[publisher guidance](../../publisher.md). Those
owners retain their procedural responsibilities. Serialize shared orchestrator
guidance, glossary, WDR index, and parent-map edits.
Current role policy is defined by the authoritative orchestrator owner.

- **AC-1 DONE** Given the adoption contract and prerequisite guidance Works,
  their boundaries and sequence define one reviewable policy outcome without
  duplicating operational procedures or weakening independent review.

  Validation: manually review ownership, dependencies, and expected adoption
  scope against current orchestration, Work, PR, cleanup, and WDR guidance.
