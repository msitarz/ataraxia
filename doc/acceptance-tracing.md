# Work acceptance

Read when assigning criterion IDs, assessing Work acceptance, or preparing
Work delivery evidence.

## Criterion status

Give each criterion a stable ID such as `AC-1`, unique within its owning Work
`README.md`. The repository-relative path scopes the ID. Use the criterion
headings in the [Work contract template](work-contract-template.md).

- `TODO` means the outcome is not yet verified from inspectable evidence.
  Planned checks, implemented tests, and failed, skipped, pending, or unrun
  checks do not establish the required outcome.
- `DONE` means an independent reviewer verified the outcome from observed
  evidence. It does not itself mean maintainer approval or merge.

Any required `TODO` criterion prevents Work completion.

## Evidence

The maintainer accepts Work outcomes based on evidence. Agent review
prepares that decision and does not replace maintainer review. Evidence depends
on the outcome:

- Implementation: code, appropriate tests, and their results in CI. Local test
  runs support preparation and debugging.
- Guidance: the changed guidance that fulfills the criteria.
- Investigation: recorded findings and, where execution is used, shell/code
  execution results retained as artifacts.
- Evaluation: recorded results required by its declared protocol.

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
   and maintainer merge. Maintainer acceptance, agent review, latest-head CI,
   and maintainer merge retain their existing responsibilities.

For a requested parent with direct leaves, apply this procedure locally to each
leaf in execution order on the accumulating branch. Retain each leaf contract
through the requested tree's final review and merge. The parent owner reviews
map updates before the executor applies them. Local acceptance permits
dependent work under
[orchestrator guidance](orchestrator.md#review-and-return); it does not
establish CI outcomes or authorize child publication. After all leaves,
independently review the parent's own outcomes and retain its contract through
merge. Any required unsupported criterion remains `TODO` and requires steering
under the evidence rules above.

For a child parent within the requested tree, retain its independently reviewed
contract through immediate-parent integration and the requested tree's merge.
The requested Work publishes its reviewed implementation and retained contracts
at that [delivery boundary](pull-requests.md#publishing).

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

After merge, keep the finished contract available until the supported
post-merge closure procedure exists. Do not add manual contract deletion or
reference-update loops. If a Work stops unsatisfied, follow the
[abandonment lifecycle](workflow.md#lifecycle).
