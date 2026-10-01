# Handoff scope growth

Establish and route a rule for delegated repository changes that grow beyond
their agreed responsibility while work is underway.

PR #93 adds Make selectors and targets, tests, contributor and agent guidance,
and a proposed WDR for the project-tool interface. This is a concrete case for
deciding when newly discovered scope should become independently reviewable
child Works.

## Acceptance

- Define observable signs that scope growth no longer fits the handoff or a
  quick human review, using the existing
  [Work scope and sizing rule](../../../workflow.md#scope-and-sizing)
  rather than restating its review-time guidance.
- Specify the stop-and-split response for both contexts: for an ad hoc handoff
  without a Work, create a parent Work and small reviewable child Works; for an
  existing Work, nest child Works in its hierarchy. Review and merge the
  planning parent before continuing the expanded scope.
- Preserve routine implementation choices within the agreed contract and the
  existing exception for explicit maintainer direction to add scope to the
  current PR; this policy must not add an approval gate for ordinary choices.
- Identify the lasting policy owner and any required reading route, linking the
  [orchestrator handoff](../../../orchestrator.md) and
  [Work lifecycle](../../../workflow.md) instead of copying their rules.

Promote the rule to its authoritative owner and add any needed reading route.
