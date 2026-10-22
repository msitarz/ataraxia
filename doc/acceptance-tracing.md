# Work acceptance

Read when assigning criterion IDs, assessing Work acceptance, or preparing
Work delivery evidence.

## Criterion status

Give each criterion a stable ID such as `AC-1`, unique within its owning Work
`README.md`. The repository-relative path scopes the ID. Use the criterion
headings in the [Work contract template](work-contract-template.md).

A criterion describes an independently assessable guarantee or condition for
the Work's one coherent outcome:

- Several scenarios may establish one guarantee and do not need separate
  criteria.
- Conditions may concern runtime behavior, guidance, Investigation findings,
  or Evaluation evidence.
- A parent's inherited constraints remain distinct from a child's local
  criteria.
- Parent acceptance verifies shared guarantees across the combined result,
  including cross-child behavior and declared system-level conditions.
- The union of child `DONE` statuses does not establish the parent's
  composition outcome.
- `TODO` means the criterion's condition or guarantee is not yet verified from
  inspectable evidence. Planned checks, implemented tests, and failed, skipped,
  pending, or unrun checks do not establish the required outcome.
- `DONE` means an independent reviewer verified the criterion's condition or
  guarantee from observed evidence. It does not itself mean maintainer approval
  or merge.
- An assignment return alone establishes neither criterion status nor Work
  completion.

Any required `TODO` criterion prevents Work completion.

## Evidence

The maintainer accepts Work outcomes based on evidence. Agent review
prepares that decision and does not replace maintainer review. Evidence depends
on the outcome:

A Work artifact is a concrete output produced or updated within the Work, such
as its contract, typed architecture, typed wiring, or implementation. An
intermediate artifact can support review or verify an acceptance criterion
without completing the Work's full outcome.

- Implementation: code, appropriate tests, and their results in CI. Local test
  runs support preparation and debugging.
- Guidance: the changed guidance that fulfills the criteria.
- Investigation: recorded findings and, where execution is used, shell/code
  execution results retained as artifacts.
- Evaluation: recorded results required by its declared protocol.

For implementation outcomes:

- Distinguish checked static contracts,
  executable composition, and delivered behavior.
- A type check supports only the static contracts it checks;
  [engineering guidance](engineering.md#reviewed-type-stubs) owns its limits
  for runtime validation and purity.
- A [walking skeleton](engineering.md#progressive-implementation) can establish
  that its exercised composition and orchestration run, but not the behavior of
  its stubbed leaves.
- Claim only behavior observed by the relevant checks or review; placeholders,
  unrun tests, and planned acceptance checks establish no passing result.

Keep execution results in their source records; do not copy test output or
check inventories into contracts, commit messages, or maintainer handoffs.
Report material failures or limitations concisely.

A plan, a declaration check, or an implemented test alone does not establish
the outcome; automated checks establish only the behavior they exercise.

Local evidence can establish acceptance before PR CI runs.

## Work delivery

1. While the contract exists, assess its outcomes using applicable checks and
   artifact review under the [check and evidence policy](validation.md). Keep
   unsupported criteria `TODO`.
2. After independent review, commit the implementation with its contract
   retained. Mark criteria `DONE` only when the independent reviewer has
   verified their outcomes. Preserve inspectable evidence in its source
   records; do not duplicate manual outcomes beside criteria. Keep unsupported
   criteria `TODO`.
3. Retain requested and descendant contracts through PR review, corrections,
   and completion. Follow [Work lifecycle](workflow.md#lifecycle) for keeping
   completed child Works and architecture artifacts through parent completion.
   Maintainer acceptance, independent review, full CI on the final reviewed
   head, and maintainer merge retain their distinct responsibilities.

For a requested parent with direct leaves, apply this procedure locally to each
leaf in execution order on the accumulating branch. Retain each leaf contract
through requested-tree integration and review under step 3 above. The parent
owner reviews map updates before the executor applies them. Local acceptance
permits dependent work under
[orchestrator guidance](orchestrator.md#review-and-return); it does not
establish CI outcomes or authorize child publication. After all leaves,
independently review the parent's own outcomes and retain its contract through
integration and PR review under step 3 above. Any required unsupported criterion
remains `TODO` and requires steering under the evidence rules above.

For a child parent within the requested tree, retain its independently reviewed
contract through immediate-parent integration and requested-tree review under
step 3 above. The requested Work publishes its reviewed implementation and
retained contracts at that [delivery boundary](pull-requests.md#publishing).

Before publication, independently review the resulting artifact and its PR
description. Publish only after that review.

Development fixups may be folded into the implementation commit; retaining
every intermediate commit or SHA is not required. A later implementation or
evidence correction invalidates the affected evidence. Return its criterion to
`TODO`, repeat applicable checks and independent review, and refresh the source
evidence before marking it `DONE` again.

Rebase the reviewed implementation onto current `master` as linear history.
Refresh commit references in existing evidence records when a rebase changes
the referenced commits.

Substantive implementation corrections update retained contracts and evidence
directly, then require refreshed review. Maintainers may remove retained
contracts or artifacts manually; this is not a Work completion step and has no
required command or publication route. Maintainer review, merge authority, and
full CI on the final reviewed head remain distinct requirements.

## Authorized closure

This former process was superseded by
[WDR 30](wdr/0030-retire-prescribed-work-and-git-cleanup.md). The heading stays
as a historical link target for retained decision and Work records; it carries
no current closure procedure or requirement.
