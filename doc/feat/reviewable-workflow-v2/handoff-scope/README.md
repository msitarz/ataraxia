# Handoff scope growth

Plan a rule for delegated repository changes that grow beyond their agreed
responsibility while work is underway. This Work defines the policy and its
owner; it does not implement or route the policy yet.

PR #93 adds Make selectors and targets, tests, contributor and agent guidance,
and a proposed WDR for the project-tool interface. This is a concrete case for
deciding when newly discovered scope should become independently reviewable
child Works.

## Acceptance

- Define observable signs that scope growth no longer fits the handoff or a
  quick human review, using the existing
  [Work scope and sizing rule](../../../workflow.md#scope-and-sizing)
  rather than restating its review-time guidance.
- Specify that the agent and orchestrator stop adding the expanded scope,
  describe a parent outcome and independently reviewable child Works, and
  merge that planning parent before starting child execution.
- Preserve routine implementation choices within the agreed contract and the
  existing exception for explicit maintainer direction to add scope to the
  current PR; this policy must not add an approval gate for ordinary choices.
- Identify the lasting policy owner and any required reading route, linking the
  [orchestrator handoff](../../../orchestrator.md) and
  [Work lifecycle](../../../workflow.md) instead of copying their rules.

The result should leave a concise policy contract ready for a separate
implementation Work. Do not update permanent guidance or execute that future
Work here.
