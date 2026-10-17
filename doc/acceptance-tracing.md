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
3. Retain requested and descendant contracts through PR review and corrections
   until closure is authorized as described below. Maintainer acceptance,
   independent review, full CI on the final closure head, and maintainer merge
   retain their distinct responsibilities.

## Authorized closure

Only the maintainer's spoken or written instruction in the session authorizes
closure of selected Works for the reviewed open PR head and covers the
resulting mechanical changes on that same PR branch. No token, approval file,
extra ceremony, or tool proof of chat authorization is required. Session
context may explicitly establish that a response such as “its ok” authorizes
the closure in question; generic implementation acceptance does not. `DONE`,
passing checks, ready-for-review status, and implementation or PR-revision
requests do not authorize closure.

The planned thin Make interface is `make work-close ARGS='path/to/README.md'`.
`ARGS` contains only Work README paths, following the existing `work-check`
convention. It reports any `TODO` criteria and pauses without repository changes
so the agent can relay the abort question to the maintainer. Only after the
maintainer explicitly confirms aborting those outcomes may the agent rerun with
`ABORT_REMAINING=true`; this flag expresses the confirmed operation, not
authorization. Cancellation, no answer, or any other response leaves repository
state unchanged. The current criterion checker accepts only `TODO` and `DONE`;
until its `ABORT` support is delivered, incomplete closure pauses and
completed-Work closure remains available through the existing Executor,
Orchestrator, and Publisher roles under this guidance.

After confirmation and checker support, closure records each remaining
criterion as `ABORT` with its reason and closes the Work and applicable
parent/dependency entries as `ABORT`; completed Works close as `DONE`. Criterion
identities and abort dispositions must remain inspectable in committed Git
history after contract deletion. The command Work chooses how to preserve that
history; it must not rely on a same-commit edit and deletion that leaves no
record.

Closure publication requires a clean state, exact reviewed and remote tips,
authorized selection, and unambiguous reference updates. Use the same reviewed
open PR branch, ordinary push, and existing hooks and signing. Refusal or
failure preserves recoverable work; do not force push, bypass protections,
publish directly to master, or open a separate closure PR. Full CI must pass
on the final closure head before maintainer merge. Git branch and worktree
cleanup is separate, post-merge work requiring verified merged closure
provenance; the planned thin interface is
`make work-cleanup PR=<number>`. Until its command Work is delivered, use
[current branch cleanup guidance](branch-cleanup.md).

The pending
[mechanical closure command Work](feat/post-merge-work-closure/command/README.md)
owns implementation. See
[orchestrator guidance](orchestrator.md#roles-and-delegation) for current
operational role ownership and
[WDR 29](wdr/0029-publish-authorized-work-closure-on-the-reviewed-pr.md) for
the decision.

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

Substantive implementation corrections after closure approval invalidate
authorization for affected Works. If their contracts were already closed,
restore the affected contracts and evidence, refresh statuses and independent
review, and obtain renewed closure instruction. Corrections before closure
update retained contracts and evidence directly. Do not add routine
verification/removal pairs or manual closure procedures. For incomplete
closure, including the current checker limitation, follow
[authorized closure](#authorized-closure).
