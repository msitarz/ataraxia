# Post-merge branch cleanup

Read this procedure after the maintainer confirms a Work PR has merged.

Keep either branch if an active PR depends on it. Before deleting a local or
remote branch, verify that its tip contains no changes beyond the revision that
was reviewed and merged. A squash merge may make Git's ancestry check
inconclusive; inspect the branch's later commits and compare its changes with
the merged revision. Check local and remote tips separately. If the working
tree is dirty or any comparison is uncertain, preserve the branch and ask the
maintainer.

When the working tree is clean and the local tip is verified, update `master`
with these separate commands:

```sh
git switch master
git fetch origin
git merge --ff-only origin/master
```

Delete a verified local branch with `git branch -d <branch>`. Use `-D` only
when the merged revision and absence of undelivered changes are confirmed,
including after a squash merge. If the remote branch still exists and its tip
is verified, delete it with `git push origin --delete <branch>`.

After deleting a merged Work branch, remove empty local Work directories left
by completed Works. Preserve directories that are active or nonempty.
