# Workspace preparation

Create a Make-owned branch worktree preparation path for agent workspaces.
Copy the source `.cache` when present, create a fresh virtual environment in
the destination with offline `ci-setup`, and verify it before reporting ready.
Do not copy or share a mutable virtual environment. If setup fails, preserve the
worktree and explain how to recover it.

Keep locked dependency synchronization, clear missing or stale environment
failures, hooks and packaging for their actual consumers, offline verification
promises, and the full audit intact. The trial-preparation map tracks the
already delivered CI-preparation outcome; [Make](../../../../../../Makefile)
owns its recipes. This target reuses the existing CI setup and verification
recipes and does not create a second CI optimizer. The measured baseline below
informed the chosen full-cache-copy direction; it does not promise a general
speedup.

## Acceptance

- **AC-1 DONE** `make worktree-create WORKTREE=/path BRANCH=work/example`
  creates a branch from local `master`, copies the source `.cache` if present,
  creates an isolated destination `.venv` without copying the source
  environment, and reports ready only after offline `ci-setup` and
  `verify-setup` succeed. Existing destinations and branches fail without
  cleanup; cache or setup failures leave the worktree available with recovery
  guidance. Verification: exercise success, destination and branch conflicts,
  missing and incomplete caches, and environment routing using temporary Git
  repositories and fake `uv` executables.
- **AC-2 DONE** Locked dependency synchronization, missing or stale environment
  failures, consumer-required hooks and packaging, offline verification, and
  the full network audit remain intact; this target reuses existing
  `ci-setup` and does not prepare hooks.
  Verification: inspect Make recipes and exercise setup and verification
  routing; compare the existing setup and CI targets for preserved behavior.
- **AC-3 DONE** The selected full-cache-copy direction has a measured baseline
  and the worktree preparation outcome follows the already delivered CI
  preparation work without adding a second CI optimizer.
  Verification: inspect the baseline measurements below and the parent Work
  dependency map and recipe reuse.

## Measured baseline

On 2026-10-02 at revision
`01a53b9aec87c4256a521ccb240fd9ea8ecc04fb`, two fresh detached worktrees were
created on macOS with installed Python 3.14.6 at `/usr/local/bin/python3.14`.
The source `.cache` measured 389 MB: 219 MB for prek, 164 MB for uv, 6 MB for
rumdl, and 24 KB for build artifacts. Each `/usr/bin/time -p` result below is
one wall-clock observation; OS caches were not flushed and there were no
repeated or networked timing runs.

| Step | Seconds | Result |
| --- | ---: | --- |
| Create empty-cache worktree | 0.10 | Passed |
| Empty-cache offline `ci-setup` | 0.22 | Failed because the prek wheel was absent |
| Create copied-cache worktree | 0.09 | Passed |
| Copy full source `.cache` with `cp -R` | 7.73 | Passed |
| Fresh offline `ci-setup` | 0.21 | Passed; installed 40 packages and built the local editable project |
| `verify-setup` | 0.17 | Passed without changes |
| `doc-check` | 1.71 | Passed across 70 files |
| Repeat offline `ci-setup` | 0.06 | Passed against the existing environment |

Worktree creation, cache copy, setup, and environment verification totaled
8.20 seconds. Including `doc-check`, the measured sequence totaled 9.91
seconds. The pytest shebang and editable `ataraxia` path resolved inside the
new worktree. Hooks, full verification, installed-wheel smoke checks, and the
network audit were not exercised. These observations support offline setup
with the copied cache on this machine; they do not establish a general speedup.

A later single run of the implemented `worktree-create` target completed in
8.25 seconds, including copying the full cache, creating the fresh environment,
and passing offline setup and verification. A subsequent `doc-check` in that
worktree passed all 70 files in 1.54 seconds. This run used the installed
Python 3.14.7 at `/Users/nzs/.local/bin/python3.14`, unlike the earlier Python
3.14.6 baseline; it is implementation evidence, not a timing comparison.
The pytest shebang and editable `ataraxia` path resolved inside the new
worktree.
