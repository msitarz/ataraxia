# 32. Resolve uncertain decomposition through bounded exploration

Date: 2026-10-22

## Status

Accepted

Amends
[31. Define outcome contracts and size for understanding](0031-define-outcome-contracts-and-size-for-understanding.md)
for how to proceed when a coherent outcome's decomposition is not yet known.
The existing whole-tree pause, maintainer decision, and planning-PR gates for a
discovered split or scope change remain in force.

## Context

Outcome-first sizing and planning avoid premature Work splits. However, an
unknown decomposition may require a small amount of typed design evidence
before a maintainer can determine whether the outcome is coherent as one leaf
or contains independently deliverable outcomes. Treating all such exploration
as expanded implementation would leave that uncertainty unresolved; allowing
implementation to grow during exploration would bypass the existing gates.

## Decision

When decomposition is unknown, permit the smallest typed architecture
exploration that answers the remaining question within the stated outcome.
Exploration may support retaining a leaf, proposing a split, or framing a
bounded Investigation. It does not authorize expanded feature implementation.
If exploration finds a split or scope change, pause the requested Work tree,
obtain required maintainer steering, and merge the concrete planning PR before
expanded implementation.

Keep composition maps, scheduling dependencies, and module architecture
distinct. Record architecture at its maturity: exploratory, reviewed, or
implemented. Update the current architectural view as reviewed boundaries
change, and retain superseded exploration with status or context that does not
leave duplicate active definitions.

## Consequences

[Work definition](../work-definition.md#decomposition-and-architectural-exploration)
owns the decomposition assessment, and
[Work workflow](../workflow.md#decisions-and-new-splits) owns pause and planning
gates. [Architecture exploration](../architecture-exploration.md) owns design
maturity and retention; the product [Architecture](../architecture.md) remains
the current product view. The
[architecture-exploration Work](../feat/outcome-driven-guidance/architecture-exploration/README.md)
carries the guidance change, subject to independent review and parent
composition. Maintainer review and merge authority and final-head CI remain in
force.
