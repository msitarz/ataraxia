# Post-merge branch cleanup

Read this procedure after the maintainer confirms a Work PR has merged.

Keep either branch if an active PR depends on it. Before deleting a local or
remote branch, verify that its tip contains no changes beyond the revision that
was reviewed and merged. A squash merge may make Git's ancestry check
inconclusive; inspect the branch's later commits and compare its changes with
the merged revision. Check local and remote tips separately. If the working
tree is dirty or any comparison is uncertain, preserve the branch and ask the
maintainer.

Identify the completed branch's checkout with `make worktree-list`. Check its
status, including untracked files, and verify its tip against the reviewed and
merged revision as above. Preserve unrelated active worktrees. Independent
clones are separate repositories and are outside this linked-worktree procedure.

Run cleanup from a surviving checkout outside the worktree being removed.
When that checkout is clean and the local tip is verified, update `master`
with these separate commands. If `master` is checked out elsewhere, use that
surviving checkout:

```sh
git switch master
git fetch origin
git merge --ff-only origin/master
```

Before deleting a branch checked out in a linked worktree, remove its verified
clean checkout:

```sh
make worktree-list
make worktree-remove WORKTREE='/absolute/path/to/completed worktree'
make worktree-list
```

The removal target retains the branch. It uses Git's normal refusal for main,
dirty, untracked, locked, and unsupported submodule worktrees; it never forces
removal, unlocks a worktree, or falls back to filesystem deletion. On failure,
stop before branch deletion, inspect the reported cause, and preserve or deliver
remaining work. Resolve the cause with the maintainer before retrying. If the
completed branch is in the main checkout, switch away from it there instead;
the main checkout cannot be removed with this target.

If a directory was already removed outside Git, normal removal may fail. After
confirming it is abandoned rather than temporarily unavailable, preview stale
registration pruning:

```sh
make worktree-prune-preview EXPIRE=now
make worktree-prune EXPIRE=now
make worktree-list
```

Pruning removes administrative records, not existing checkout directories. Both
targets require an explicit Git expiry date; `now` includes newly missing
directories, while an older cutoff retains newer records. Preview and execution
must use the same expiry. Pruning is repository-wide: inspect every proposed
removal and proceed only if all are confirmed abandoned. Locked registrations
are preserved. If any path is uncertain, stop; do not silently prune it. On a
prune failure, inspect the error and retained registrations before retrying;
branch deletion must wait for successful cleanup. Prefer normal removal when the
directory exists. See the
[Git worktree manual](https://git-scm.com/docs/git-worktree) for expiry and
locking details.

Delete a verified local branch with `git branch -d <branch>`. Use `-D` only
when the merged revision and absence of undelivered changes are confirmed,
including after a squash merge. If the remote branch still exists and its tip
is verified, delete it with `git push origin --delete <branch>`.

After deleting a merged Work branch, remove empty local Work directories left
by completed Works. Preserve directories that are active or nonempty.
