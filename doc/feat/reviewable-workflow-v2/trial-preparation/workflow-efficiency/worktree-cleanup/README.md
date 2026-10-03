# Worktree cleanup

Complete post-merge cleanup by removing finished linked Git worktrees and their
registration through Make targets. Agent worktrees currently accumulate:
[branch cleanup](../../../../../branch-cleanup.md) covers branches and empty
Work contract directories but omits Git worktree removal, while the
[Makefile](../../../../../../Makefile) exposes creation without cleanup.

## Outcome and ownership

Update `doc/branch-cleanup.md`, the existing owner of post-merge cleanup, to
identify the completed branch's linked worktree, verify it contains no
undelivered work, and remove it through a Make proxy for `git worktree remove`.
Run cleanup from a surviving checkout outside the removal target. Remove the
linked worktree before deleting its checked-out branch; retain the existing
merged-revision comparison, dependency, `master` update, remote-tip
verification, and maintainer gates. A merged PR does not justify removing
another active worktree or losing later commits or local changes.

Provide Make proxies for listing worktrees, removing an explicitly selected
linked worktree, and pruning stale registration when its directory was already
removed externally, for example with `rm`. Prefer `git worktree remove` for
normal cleanup; `git worktree prune` removes administrative records, not an
existing checkout. Document those distinctions and executable examples at the
procedure owner; [CONTRIBUTING.md](../../../../../../CONTRIBUTING.md) links to
the procedure rather than duplicating it. See the
[Git worktree manual](https://git-scm.com/docs/git-worktree).

Expose prune preview and report its repository-wide scope and expiry behavior;
apply the same expiry choice to preview and execution. Do not silently prune
other missing registrations or treat a temporarily unavailable path as proven
abandoned. Preserve locked worktrees. Normal removal must retain Git's refusal
for dirty, untracked, locked, main, and unsupported submodule worktrees without
automatic force, unlocking, or fallback filesystem deletion. Explain recovery
when removal or pruning fails; branch deletion must not continue on a failure.

Choose the small Make interface at implementation time, consistent with
`worktree-create` and `WORKTREE`; validate required input, quote paths safely,
and propagate Git failures. Cleanup must work without installing dependencies
or preparing a virtual environment. Keep filesystem removal and registration
cleanup distinct from deleting branches and empty Work contract directories.

## Acceptance

- **AC-1 DONE** Make exposes discoverable worktree listing, explicit removal,
  and prune preview/execution proxies. Removing a clean completed linked
  worktree removes its directory and registration while retaining its branch
  for the subsequent verified branch-deletion step.
  Verification: exercise actual Make targets against a disposable repository;
  inspect `git worktree list`, directory existence, and surviving branch refs.
- **AC-2 DONE** Missing input and failed or unsafe removals preserve data and
  report failure without force or filesystem fallback. Main, dirty, untracked,
  locked, and unrelated live worktrees remain intact; paths with spaces and
  shell metacharacters are handled literally.
  Verification: use focused integration tests for actual target invocations,
  statuses, refs, registrations, and file contents in those cases.
- **AC-3 DONE** A directory removed outside Git has its stale registration
  previewed and pruned through Make with explicit expiry handling, while live
  and locked registrations survive. Repository-wide effects are disclosed.
  Verification: create live, missing, and locked fixture worktrees; compare
  preview with execution under the same expiry and inspect retained entries.
- **AC-4 DONE** The post-merge procedure removes verified linked worktrees
  before local branch deletion, handles already-removed directories, and
  preserves existing review, dependency, uncertainty, and remote-branch gates.
  Verification: walk through normal, squash-merged, later-commit, dirty,
  dependent-PR, and failed-cleanup cases; run `make help`, documentation checks,
  and the focused integration tests through Make.

## Execution gate and limits

This PR adds only this Work plan and its parent TODO entry. Implement after
the reviewed plan merges, in an independent PR from current `master`. This
planning delivery does not delete any accumulated worktrees or change the
current cleanup procedure.

Coordinate wording with [Worktree language](../worktree-language/README.md), but
do not make cleanup depend on that terminology-only change. Independent shallow
clones from [Shallow executor clones](../shallow-executor-clones/README.md) are
separate repositories and are outside linked-worktree removal. No blanket
cleanup, scheduled garbage collection, or change to creation and setup belongs
in this Work. Reassess the actual diff against the existing review target.
