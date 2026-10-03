# Work-type simplification

Remove Rewrite as a special Work type and treat the delivery as ordinary Work,
without a special process, branch-default exception, or compatibility alias. The
current [Work workflow](../../../../../workflow.md) has a “Prototypes and
rewrites” heading and dedicated rewrite contract paragraph. Its internal
Prototype link and the [glossary](../../../../../ubiquitous-language.md)
Prototype row use that combined anchor;
[CONTRIBUTING.md](../../../../../../CONTRIBUTING.md#work-branches-review-and-merge)
also names “Prototype or rewrite” as an example of an explicitly approved base
exception. These are the initial verified surfaces for future implementation.

## Scope and ownership

The Work workflow will retain ordinary scope, contract, lifecycle, review, and
preservation rules, rename the heading to “Prototypes,” and remove the
rewrite-specific paragraph and type-specific examples. Repair all affected
anchors and the existing glossary Prototype link. CONTRIBUTING retains its
general requirement for explicit branch/base approval without a Rewrite
example. Preserve Prototype and Investigation as distinct existing Works.

Ordinary Works may state preservation, migration, and retirement requirements
when relevant. Do not relocate the rewrite checklist to another owner or invent
a replacement type. Ordinary uses of the verb “rewrite,” including Git
publication and editing contracts, are outside the type removal.

## Acceptance

- **AC-1 DONE** Current guidance has no Rewrite Work type, special process,
  type-specific base exception, or alias. Ordinary Work contracts can express
  relevant preservation and migration outcomes without a separate checklist.

  Verification: inspect the Work and contribution owners and walk through an
  ordinary replacement delivery with preserved behavior and migration needs.
- **AC-2 DONE** The Prototypes heading and all active links use the repaired
  anchor; Prototype and Investigation meanings and ordinary Work lifecycle,
  review, preservation, and explicit base-approval rules remain intact.

  Verification: follow internal and glossary links, scan active guidance for
  the old anchor and type references, and run `make doc-format` and
  `make doc-check`.
- **AC-3 DONE** Historical accepted decisions and immutable evidence remain
  intact; unrelated Git and contract-editing uses of “rewrite” retain their
  meaning. Overlapping owner changes are reconciled against current master.

  Verification: classify remaining rewrite references, compare history and
  unrelated guidance with the starting revision, and review affected owners
  alongside any integrated Evaluation guidance.

## Execution gate and limits

This plan changes only this README and its parent TODO entry. Implement in an
independent PR from current `master` after the plan and parent map merge.
[PR 123](https://github.com/msitarz/ataraxia/pull/123) plans Evaluation guidance
on shared workflow/glossary surfaces; reconcile its integrated outcome and owner
links without implementing that plan here or using its branch as a base.

Aim for one
[five-minute review outcome](../../../../../workflow.md#scope-and-sizing):
removal of the special type with ordinary Work rules preserved. Reassess the
actual implementation and split for review before expanding if necessary. Follow
the [WDR workflow](../../../../../wdr-workflow.md) for consequential choices or
amendments; routine wording need not require a record. This plan adds no WDR,
glossary definition, code change, or new lifecycle.
