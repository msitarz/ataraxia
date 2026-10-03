# Worktree language

Extend the existing [glossary](../../../../../ubiquitous-language.md) with the
canonical Worktree term and remove Workspace as its synonym from current
guidance. Verified surfaces include CONTRIBUTING's “isolated agent workspace,”
the Makefile help heading “Workspaces,” the parent's “Workspace preparation”
navigation and AC-3, and the trial-preparation README's preparation wording.
The [documentation owner](../../../../../README.md#vocabulary) already requires
consistent glossary terms; use that owner and current reading routes to prevent
new aliases rather than introducing another terminology framework.

## Intended meaning and owners

The future glossary entry will define Worktree as a Git working tree/checkout,
distinct from a Work's contract directory, a branch/ref, the Git repository,
and a generic temporary directory or virtual environment. Linked worktrees
have independent working files, index, and HEAD while sharing Git objects and
repository refs. This is not a security or permission boundary and does not
create independent full repositories.

Use Worktree/worktree with normal prose casing; add no Workspace synonym or
deprecated alias. The glossary owns meaning.
[CONTRIBUTING.md](../../../../../../CONTRIBUTING.md) owns setup and the Make
interface; [orchestrator guidance](../../../../../orchestrator.md) owns leaf-use
rules, and [branch cleanup](../../../../../branch-cleanup.md) owns post-merge
removal. Authors will use the existing glossary and documentation
vocabulary/review routes, with focused links rather than copied definitions or a
new owner.

## Acceptance

- **AC-1 TODO** The existing glossary contains one Worktree entry with the
  distinctions and Git sharing boundaries above, linked to procedure owners.
  Current guidance uses that meaning without aliases or isolation overclaims.

  Verification: inspect the glossary and owner routes; classify examples of
  a linked checkout, Work directory, branch, repository, and temporary venv.
- **AC-2 TODO** Active authoritative guidance, retained Work contracts, and
  navigation use canonical worktree language, and Make help says “Worktrees.”
  No Workspace alias remains in current guidance. Existing vocabulary and
  review rules make the single glossary meaning discoverable to future authors.

  Verification: scan case-insensitively for workspace references, manually
  classify leftovers as current aliases, historical identities, external
  verbatim references, or unrelated concepts, and inspect reading routes.
  Run `make help`, scoped `make doc-format` and `make doc-check`.
- **AC-3 TODO** Terminology changes preserve `worktree-create`, `WORKTREE`,
  creation, working-tree separation, cache/environment setup, validation, and
  CI guarantees. Historical evidence and decision identities stay intact;
  unrelated code variables and removed-contract provenance are not relabeled.

  Verification: review the diff against the starting revision, compare Make
  recipes and guidance guarantees, and inspect the package-smoke temporary
  directory and historical acceptance-marker paths for unintended changes.

## Execution gate and limits

This plan changes only this README and its parent TODO entry. Implement in an
independent PR from current `master` after this plan and parent map merge.
Reconcile concurrent owner edits without stacking on another planning branch.
Aim for one
[five-minute review outcome](../../../../../workflow.md#scope-and-sizing): one
precise shared term with current aliases removed. Reassess the actual
implementation and split for review before expanding if needed.

The `workspace` variable in `script/smoke_installed_package.py` denotes a
temporary installed-wheel directory, not a Git worktree; code cleanup is out
of scope. `workspace-preparation/README.md` literals in
`test/integration/test_makefile.py` preserve historical coverage provenance;
do not fabricate a rename of that removed Work. Preserve accepted decision
bodies and immutable evidence identities while correcting current navigation.
Do not require a blanket zero-match scan, new journal, testing framework, or
tests that merely mirror prose. No glossary or Make behavior changes occur in
this planning delivery.
