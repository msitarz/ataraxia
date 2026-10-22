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
- Preserve reviewed design when converting `.pyi` to `.py`, recheck the
  conversion, and prevent duplicate interfaces from shadowing unchecked
  implementation.
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
- Remove the current cleanup process first and defer its replacement;
  distinguish Work/artifact closure from branch/worktree cleanup.
- Retain completed Works and typed architecture through parent completion;
  parent completion is not deletion authorization.

## Verified baseline and affected owners

The maintainer reported useful experience with making intent visible early.
Reduced drift, lower cost, and reliable use of cheaper models remain unproven;
this plan makes no efficacy claim from that experience.

Baseline is `c08b883d0d58a4c224136b2ff4ea9fc8cae83f6c` on `master`.

- [Work workflow](../../workflow.md#scope-and-sizing) currently applies the
  five-minute target to the complete expected change and actual diff;
  outcome-contract guidance will replace that meaning and its role reminders.
- [Work template](../../work-contract-template.md) currently gives each
  acceptance criterion one outcome; the new contracts deliberately use one
  outcome per Work and acceptance conditions within it.
- [Work acceptance](../../acceptance-tracing.md#authorized-closure) and
  [Work workflow](../../workflow.md#lifecycle) currently prescribe selected
  contract removal after explicit authorization;
  [branch cleanup](../../branch-cleanup.md) separately prescribes post-merge Git
  operations.
- [Post-merge closure](../post-merge-work-closure/README.md) has delivered
  lifecycle guidance and pending
  [command](../post-merge-work-closure/command/README.md) and
  [adoption](../post-merge-work-closure/adoption/README.md) Works; the first
  child will retain these records and explicitly supersede their unfinished
  plans rather than build them.
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
