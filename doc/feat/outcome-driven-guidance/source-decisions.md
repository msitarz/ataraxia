# Source decisions for outcome-driven guidance

This local summary preserves the accepted direction from the
[maintainer conversation](https://chatgpt.com/share/6ad9badc-3914-83ec-a40e-f1f6ace8898b).
It is planning input, not evidence that migration is delivered. The Work
contracts carry future acceptance conditions; current guidance remains
authoritative until changed through those Works.

## Accepted direction

- Begin with one Work per coherent outcome; acceptance criteria are verifiable
  conditions or behaviors for that outcome, while inherited constraints remain
  distinct.
- Aim to understand intent, acceptance conditions, constraints, and
  architectural relationships in about five minutes; implementation review stays
  substantive and uncapped.
- Keep outcome hierarchy separate from module hierarchy; parent composition and
  scheduling dependencies are distinct.
- Parents establish essential concepts, invariants, responsibilities, dependency
  direction, and effect limits without specifying every signature up front.
- Ask whether decomposition is needed: yes, no, or unknown; resolve unknown
  through minimal typed architecture exploration and preserve findings if the
  Work splits.
- Deliver vertical outcomes that add behavior; preserve prior outcomes through
  regression checks rather than restating their acceptance conditions.
- Treat a parallel-shard outcome as one leaf unless an isolated worker delivers
  independent value; this illustration does not approve product behavior.
- Distinguish exploratory, reviewed, and implemented typed architecture; permit
  reviewed boundary changes with explicit reviewed justification and keep
  private helpers flexible.
- Keep the current architectural view accurate when later children change
  shared architecture, and mark retained exploration and superseded design
  distinguishably through lightweight status or explanation.
- Preserve reviewed design when converting `.pyi` to `.py`, recheck the
  conversion, and prevent duplicate interfaces from shadowing unchecked
  implementation; retained design can be stored or labeled separately outside
  active module resolution.
- Progress as useful through conditional architecture exploration, real typed
  wiring with stubbed leaves, a thin executable skeleton with fake adapters,
  behavioral tests and implementation, and engineering review.
- Review test intentions early and actual assertions later; static checks,
  executable wiring, and completed behavior provide different evidence, and
  placeholders prove no acceptance outcome.
- Validate invariants at their owning boundary; pure core logic consumes trusted
  typed values, and static typing alone proves neither runtime validation nor
  purity.
- Assign inherited non-functional guarantees a local, architectural, or system
  verification scope; state quantitative thresholds with conditions and verify
  parent composition independently of child completion.
- Review a focused engineering rule against one immutable revision using old/new
  functions and rule-appropriate caller, type, and module context.
- Support PASS, VIOLATION, NOT_APPLICABLE, and UNCERTAIN judgments,
  evidence-backed findings, deduplication, and responsible owner judgment.
- Bound repair; five corrections is a fallback cap, with earlier stopping on
  recurrence, oscillation, conflict, no progress, or architectural change.
- Remove obsolete rules at their owners; avoid mandatory phase agents,
  speculative review automation, and more process before trying two or three
  representative Works.
- Require at least one real Work delivery in that future trial, exercising
  applicable architecture, wiring, testing, implementation, and review in
  proportion to the change; other cases may be walkthroughs with explicit
  evidence limits, and this plan authorizes no unrelated implementation.
- Retire both prescribed Work/artifact closure and post-merge branch/worktree
  cleanup first so the maintainer can handle cleanup manually and observe its
  natural evolution before defining another process.
- Retain completed Works and typed architecture through parent completion;
  parent completion is not deletion authorization, and the maintainer removes
  retained architecture artifacts manually later without a new cleanup process.
  The maintainer later authorized one exact exception: delete the post-merge
  closure parent, command, and adoption contracts named in the cleanup
  retirement Work. This does not authorize deleting other Works or artifacts.

## Verified baseline and affected owners

The maintainer reported useful experience with making intent visible early.
Reduced drift, lower cost, and reliable use of cheaper models remain unproven;
this plan makes no efficacy claim from that experience.

Baseline is `c08b883d0d58a4c224136b2ff4ea9fc8cae83f6c` on `master`.

- At the verified planning baseline,
  [Work workflow](../../workflow.md#scope-and-sizing) applied the five-minute
  target to the complete expected change and actual diff.
  [WDR 31](../../wdr/0031-define-outcome-contracts-and-size-for-understanding.md)
  records the delivered policy: the heuristic covers understanding the outcome
  and contract, while implementation review remains substantive and uncapped.
- At the verified planning baseline, the
  [Work template](../../work-contract-template.md) described one outcome per
  acceptance criterion. The delivered contract policy now gives each Work one
  coherent outcome and uses criteria for independently assessable conditions or
  guarantees; see
  [WDR 31](../../wdr/0031-define-outcome-contracts-and-size-for-understanding.md)
  and the current
  [template](../../work-contract-template.md#acceptance-criteria),
  [definition](../../work-definition.md), and
  [acceptance guidance](../../acceptance-tracing.md).
- The current writing standard for Work contracts and guidance is owned by
  [Documentation ownership](../../README.md#writing). The outcome-contract
  Work delivered this policy and its template, guidance, and review routes.
- At the verified planning baseline,
  [Work acceptance](../../acceptance-tracing.md) and
  [Work workflow](../../workflow.md) prescribed selected contract removal, and
  [branch cleanup](../../branch-cleanup.md) prescribed post-merge Git
  operations. WDR 30 retires those procedures; WDR history and Git preserve
  their prior states without requiring retention of the obsolete contracts.
- The post-merge closure lifecycle guidance was delivered. The closure parent,
  command, and adoption contracts are removed under the exact exception in the
  [cleanup retirement Work](retire-cleanup/README.md); Git history preserves
  their prior states. The command and adoption outcomes were never implemented.
  [WDR 30](../../wdr/0030-retire-prescribed-work-and-git-cleanup.md) records
  the current cleanup rationale.
- [Engineering](../../engineering.md), [testing](../../testing.md), and
  [engineering review](../../engineering-review.md) already own boundaries, pure
  decisions, meaningful tests, and design judgment; extend those owners rather
  than creating a parallel rule system.
- [Existing workflow trial](../reviewable-workflow-v2/live-trial/README.md) and
  its
  [trial contract](../reviewable-workflow-v2/trial-preparation/trial-contract/README.md)
  still require a broader protocol and a familiar parallel feature; the
  representative trial must explicitly reconcile these pending plans rather than
  inherit them silently.

## Decision history and implementation boundary

[WDR workflow](../../wdr-workflow.md) governs consequential changes when the
implementation Works change current guidance. Existing records, particularly
[review sizing](../../wdr/0003-size-works-for-maintainer-review.md),
[retention](../../wdr/0028-retain-work-contracts-until-authorized-closure.md),
and
[closure publication](../../wdr/0029-publish-authorized-work-closure-on-the-reviewed-pr.md),
need their normal amendment or supersession treatment there. This planning PR
neither rewrites accepted history nor declares new guidance implemented.
