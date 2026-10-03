# Shallow executor clones

Prepare executors from a shallow clone of the local repository so ordinary
history browsing cannot supply removed implementations or earlier answers.
For empirical evaluations that exclude history, make the permitted inputs and
actual isolation inspectable before execution.

Current [orchestrator guidance](../../../../../orchestrator.md) requires linked
Git worktrees. They isolate edits but share the source repository's history.
The [preparation target](../../../../../../Makefile) creates a branch from local
`master`, copies caches, and prepares a fresh locked environment. Replace the
executor preparation mechanism while preserving those setup guarantees and
the existing independent review and delivery gates.

## Proposed outcome and boundaries

- A Make-owned preparation target creates an independent shallow clone from the
  local repository, with one selected branch, depth one, and no tags. Use
  `--no-local` or a `file://` URL: plain local-path cloning uses local
  optimizations that ignore `--depth`. Do not borrow objects through alternates
  or reference repositories. See the
  [Git clone manual](https://git-scm.com/docs/git-clone).
- Record and verify the selected base commit before handoff; retain local
  `master` as the default under
  [contribution rules](../../../../../../CONTRIBUTING.md#work-branches-review-and-merge).
  Reject an unexpected base or existing destination without overwriting it.
  Cloning transfers committed state; uncommitted source edits are not inputs.
- Remove the source remote after preparation so routine fetches cannot deepen
  the clone. The executor works on its assigned branch and returns local
  commits and evidence. The orchestrator retains full history and imports the
  result for independent review, corrections, rebasing, and publication.
  Preserve the required evidence and cleanup commit order under
  [acceptance tracing](../../../../../acceptance-tracing.md#work-delivery-commits).
- Preserve cache reuse, a fresh virtual environment, locked offline setup,
  environment verification, and recoverable setup failures. Do not share a
  mutable virtual environment or silently fall back to a full-history clone.
- For an evaluation that excludes history, declare its frozen base, permitted
  files and references, session freshness, and filesystem and network access.
  Check current-tree reports, answer fixtures, and links for prohibited prior
  results; shallow history does not remove them. Prepare fresh sessions without
  inherited answers. Verify the declared restrictions before the run; if they
  cannot be established, report the blocker rather than claim isolation.

A shallow clone removes historical examples from ordinary Git navigation; it
does not prevent reuse of patterns in current code. Removing the remote is a
convenience restriction: an agent with access to the original repository can
still read its history or fetch directly from its path. Describe that exposure
accurately. Evaluations needing enforced exclusion must use an environment
that denies source-repository reads and unauthorized fetch or reference access.
This Work does not build a new sandbox or network-control system.

## Ownership and dependencies

The Make target and its focused tests own preparation behavior;
[CONTRIBUTING.md](../../../../../../CONTRIBUTING.md) owns its use and setup;
[orchestrator guidance](../../../../../orchestrator.md) owns executor handoff
and artifact return. A proposed WDR explains the change from linked worktrees
under the [WDR workflow](../../../../../wdr-workflow.md); current guidance
remains the authoritative rule after adoption.

Coordinate with [Evaluation workflow](../evaluation-workflow/README.md) for
permitted resources, contamination, and verified isolation. That Work owns
general evaluation guidance; this Work contributes the concrete clone and
history-access requirements without creating a second evaluation owner. Until
that owner exists, preserve the requirements here for integration rather than
claiming that Evaluation is already an adopted Work kind. Coordinate with
[Worktree language](../worktree-language/README.md) so independent clones are
not described as linked worktrees.

## Acceptance

- **AC-1 TODO** Make-owned executor preparation creates a depth-one local clone
  at the recorded expected base with only the selected initial branch, no tags,
  no object alternates, and no source remote after preparation. Older source
  commits cannot be read from its object database. Existing destinations and
  unexpected bases fail without overwriting data.
  Verification: use a temporary local repository with multiple commits,
  branches, and tags; inspect the shallow boundary, refs, object availability,
  remote configuration, and both failure cases.
- **AC-2 TODO** Preparation preserves locked offline setup, cache reuse, a fresh
  environment, readiness verification, and recovery instructions on setup
  failure, without a full-history fallback.
  Verification: exercise the actual target with prepared caches and missing
  setup inputs; inspect environment isolation and failure recovery against
  the existing preparation guarantees.
- **AC-3 TODO** Handoff and artifact-return guidance uses the shallow clone for
  executors and full history for the orchestrator. The documented import path
  preserves executor changes, the verified implementation/evidence commit,
  and later cleanup commit, including corrections in the same executor session.
  Verification: walk a temporary two-commit delivery and correction through
  local import, review, and rebase; check content, order, and the unchanged
  publication, maintainer-review, and CI gates.
- **AC-4 TODO** Evaluation input guidance distinguishes absent local history
  from enforced access restrictions, accounts for current-tree answers and
  inherited context, and requires pre-run verification when history is excluded.
  Verification: inspect a clean fixture, a fixture containing prior results,
  and a shallow clone whose original repository remains readable; confirm
  that exposure or unavailable enforcement is reported before execution.
- **AC-5 TODO** Authoritative preparation and orchestration guidance agrees
  with the actual tool, and a proposed WDR records rationale, alternatives,
  and limits without presenting plan approval as policy adoption.
  Verification: inspect affected owners, the WDR and index, and the reading
  routes; run documentation and acceptance-declaration checks.

## Execution gate and limits

This PR adds only this plan and its parent map entry. Merge the reviewed plan
before implementation; it does not replace current preparation rules or
authorize evaluation trials. Reassess the complete implementation against the
[review target](../../../../../workflow.md#scope-and-sizing) before handoff;
split independently reviewable child Works if necessary before execution.

Do not change model selection, review topology, current-code reuse policy, or
GitHub publication ownership. Hard sandbox implementation and comparative
performance trials require separate bounded Works and authorization. Record
limitations without claiming that clone preparation alone prevents history
access or establishes evaluation validity.
