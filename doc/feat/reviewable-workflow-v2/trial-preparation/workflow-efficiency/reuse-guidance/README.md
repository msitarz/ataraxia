# Reuse during Work planning and review

Make the existing
[repair and scope principle](../../../../../change-rules.md#fix-the-underlying-problem)
explicit at Work definition and orchestrator review, so plans address the
remaining required gap before introducing machinery or dividing avoidable
complexity into more Works.

The current repair owner already prefers one authoritative implementation,
small cohesive fixes, and no speculative abstractions. The
[Work workflow](../../../../../workflow.md) describes contracts and sizing but
does not explicitly apply that principle to defining the remaining gap. The
[orchestrator owner](../../../../../orchestrator.md) requires splitting changes
that exceed the review target without first explicitly assessing simplification
and reuse.

## Works

- **DONE** Work definition: applied existing repair and scope rules to
  inspect current machinery, reuse suitable paths, and define the remaining gap.
- **TODO** [Orchestrator review](orchestrator-review/README.md): assess
  simplification and reuse before requesting infrastructure or splitting scope.

Orchestrator review depends on the integrated Work-definition guidance in
[the Work workflow](../../../../../workflow.md). Merge this parent map before
child delivery. Each leaf changes one guidance owner and presents one review
question.

These Works operationalize existing policy and need no new WDR. They do not
add an inventory, checklist, report, guidance owner, runtime tooling, or a
requirement to reuse an abstraction whose meaning does not fit. Actual required
safeguards, independent review, maintainer review and merge control, CI, and the
approximately five-minute review target remain in force.

After adoption, rewriting the current Mermaid validation Works and a fresh
Luna-medium redo with an informal comparison are downstream work. This parent
does not change their contracts, create evaluation or comparison artifacts, or
change the formal live-trial protocol.

## Acceptance

- **AC-1 TODO** Both child outcomes are integrated into `master`, with their
  lasting guidance at the existing owners and no duplicate reuse policy.
  Validation: inspect integrated child delivery evidence and the two owner
  sections against this map.
- **AC-2 TODO** The integrated guidance supports defining only a remaining gap
  and assessing avoidable complexity before splitting, while retaining the
  required safeguards and conditional fit of reuse stated above.
  Validation: independently walk through an already-fulfilled requirement,
  a genuine missing capability, and an oversized change with necessary
  safeguards; inspect the resulting guidance for all three cases.
