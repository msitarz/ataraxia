# Work acceptance

Read when assigning criterion IDs, assessing Work acceptance, or preparing
verification and cleanup commits.

## Criterion status

Give each criterion a stable ID such as `AC-1`, unique within its owning Work
`README.md`. The repository-relative path scopes the ID. Use the criterion
headings in the [Work contract template](work-contract-template.md).

- `TODO` means the outcome is not yet verified from inspectable evidence.
  Planned checks, implemented tests, and failed, skipped, pending, or unrun
  checks do not establish the required outcome.
- `DONE` means an independent reviewer verified the outcome from observed
  evidence. It does not itself mean maintainer approval or merge.

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

## Work delivery commits

1. While the contract exists, assess its outcomes using applicable checks and
   artifact review under the [check and evidence policy](validation.md). Keep
   unsupported criteria `TODO`.
2. After independent review, commit the implementation and retained contract
   with verified criteria marked `DONE`. Preserve inspectable evidence in its
   source records; do not duplicate manual outcomes beside criteria. Keep this
   verified implementation/evidence commit before the separate cleanup
   commit. Work deliveries with acceptance criteria require both commits and
   must not be squashed.
3. In the cleanup commit, remove the contract and update the parent map. Review
   tests under [test ownership](test-ownership.md) and retain regression tests.

For a requested parent with direct leaves, apply this procedure locally to each
leaf in execution order on the accumulating branch. Keep each leaf's verified
retained-contract commit followed by its separate cleanup/map commit before the
next leaf's pair. The parent owner reviews map updates before the executor
applies them. Local acceptance permits dependent work under
[orchestrator guidance](orchestrator.md#review-and-return); it does not
establish CI outcomes or authorize child publication. After all leaves, retain
the parent's own independently reviewed verification and later cleanup pair. Any
required unsupported criterion prevents its Work's cleanup and requires steering
under the evidence rules above.

For a child parent within the requested tree, commit its independently verified
implementation with its contract retained. Its immediate parent reviews that
contract and subtree integration before recording the child's separate cleanup
and map update. Preserve leaf and parent verification/cleanup order when
integrating subtree commits into linear history. The requested Work completes
its own reviewed pair after child integration; publication occurs at that
[delivery boundary](pull-requests.md#publishing).

Before first publication, independently review both commits, the resulting
artifact, and its PR description. Publish the reviewed verification and cleanup
sequence only after that review.

Development fixups may be folded into the verified implementation/evidence
commit; retaining every intermediate commit or SHA is not required. A later
implementation or evidence correction invalidates the affected evidence. Return
its criterion to `TODO`, repeat applicable checks and independent review, and
refresh the source evidence before marking it `DONE` again. If the contract was
removed, restore it in a corrective evidence commit before making a separate
cleanup commit.

Rebase the completed sequence onto current `master` as linear history while
preserving the verified implementation/evidence commit and the later cleanup
commit in that order. Refresh commit references in their existing evidence
records when a rebase changes the referenced commits. The rebase may replace
commit IDs; it must not combine or discard either required commit.

## Limits

Any required `TODO` criterion prevents completion and cleanup. If a Work stops
unsatisfied, follow the [abandonment lifecycle](workflow.md#lifecycle).
Git retains removed contracts; evidence stays in its existing source records.
[Test ownership](test-ownership.md) covers evidence for removed adoption probes.
