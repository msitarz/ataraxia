# Cleaner trial observations

This record captures the actual post-merge cleanup for
[PR #271](https://github.com/msitarz/ataraxia/pull/271), not a simulated
operation.
The reviewed branch was `work/cleaner-guidance-luna` in
`/private/tmp/ataraxia-cleaner-guidance-luna`; reviewed head
`bc59e3ba854fea590d5a91ae737eab59b1792411` merged as
`e83eb582add40d96b08eb2d1607261d030b401aa`.

## Checks and cleanup

The cleaner checked the local branch and PR head against the reviewed revision,
compared the reviewed and merge trees, checked dependency and worktree state
(including untracked files), fast-forwarded `master`, and removed the named
worktree with `make worktree-remove`. Because this was a squash merge, it then
removed the verified local branch with `git branch -D` after the change
comparison. No remote branch deletion was performed.

Root's read-only post-cleanup observations confirmed `master` at the merge,
the named worktree and local branch absent, the reviewed/merge tree diff empty,
and unrelated PR #254 plus all four detached measurement trees retained.

## Remote-ref deviation

The cleaner read the origin remote-tracking ref concurrently with `git fetch`,
then initially reported the remote tip as verified. That ordering does not
establish a fresh remote observation. In one report clarification, the cleaner
said the observed ref was a cached value consistent with the PR head; fetch
removed it, and the ref was absent after fetch. No live remote tip was verified.
No remote deletion occurred. The local checks and scoped removals were verified,
but the remote-tip check was not; this was not a fully compliant trial.

The cleaner performed zero operational retries or cleanup correction rounds.
There was one report clarification/correction, tracked separately from
executor correction rounds. Afterward, root steered future cleaner runs to
complete fetch before any ref read or comparison, local or remote, and report
an absent post-fetch remote ref separately.

No timing, cost, or speed claim follows from this occurrence.
