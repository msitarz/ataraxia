# Assess reuse before expanding delivery structure

Apply the integrated [Work-definition guidance](../../../../../../workflow.md)
at the [orchestrator review owner](../../../../../../orchestrator.md) before
requesting new infrastructure or splitting an oversized implementation.

First assess whether simplification and reuse can fulfill the actual required
outcome with less machinery or review scope. Link to the
[Work workflow](../../../../../../workflow.md) and underlying
[repair owner](../../../../../../change-rules.md#fix-the-underlying-problem)
instead of duplicating their policy. Apply this to expected-change handoff
review and actual-diff publication review, consolidating wording where useful.

The existing split requirement still applies when the necessary change exceeds
the approximately five-minute review target. Preserve actual required
safeguards, independent review, maintainer review and merge control, full CI,
isolated worktrees, and the explicit maintainer scope exception. Reuse is
conditional on fit; simplification cannot weaken a required outcome or gate.

Deliver after Work definition is integrated into `master`. Scope is the
existing orchestrator guidance and ordinary Work completion updates. Add no
mandatory inventory, checklist, report, new owner, infrastructure, or empirical
protocol; do not change Mermaid Works or the formal live trial.

## Acceptance

- **AC-1 TODO** Expected-change and actual-diff review guidance assess
  simplification and suitable reuse before requesting infrastructure or
  partitioning an oversized implementation.
  Validation: independently inspect both review checkpoints and walk through
  a plan whose complexity can be removed by using an existing command; confirm
  simplification is assessed before adding machinery or children.
- **AC-2 TODO** When simplification cannot meet the actual required outcome
  within the review target, the existing independently reviewable split and
  parent-plan review rules still apply, with required safeguards and gates
  intact.
  Validation: independently walk through an oversized change with necessary
  safeguards and inspect the whole affected sections for preserved
  independent review, maintainer control, CI, isolation, and scope exceptions.
- **AC-3 TODO** The clarification links to the existing definition and repair
  owners without duplicating policy or requiring new planning artifacts or
  mismatched abstraction reuse.
  Validation: independently compare the diff with the integrated Work-definition
  guidance, review related sections as a whole, and run `make doc-check` plus
  `make ac-check` for this README.
