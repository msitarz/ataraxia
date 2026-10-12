# Mechanical PR publisher

Read when carrying out mechanical PR publication. Anyone preparing a rewrite of
a published branch reads the [rewrite procedure](#published-branch-rewrites)
before rebase. The assigning orchestrator owns role, model, effort, reviewed
inputs, and publication accountability under
[orchestrator guidance](orchestrator.md#roles-and-delegation). The publisher is
an operational subagent, distinct from a Work leaf executor, and need not read
orchestrator guidance or PR description preparation instructions to execute this
procedure. Read the
[publication requirements](pull-requests.md#publication-requirements) for
ready-PR meaning and the final-head CI gate.

## Publication procedure

The handoff names this guidance, the worktree, exact reviewed commit, approved
title and description file, and existing PR when updating. Identify the reviewed
description contents with a digest or an immutable copy so the publisher can
verify the file has not changed. Include explicit repository or base overrides
only when authorized; a rewrite also requires the expected remote commit
recorded before rebase under the [rewrite procedure](#published-branch-rewrites)
below.

Resolve the repository, remote branch, and base from repository and existing-PR
metadata unless explicitly overridden, following
[contribution branch rules](../CONTRIBUTING.md#work-branches-review-and-merge)
for a Work or [ordinary change bases](../CONTRIBUTING.md#submitting-a-change)
otherwise. Check that metadata agrees, the worktree is clean including untracked
files, HEAD equals the reviewed commit, and title and description match the
approved inputs. Check the remote branch before pushing: ordinary updates must
preserve all remote commits, and rewrites must use the explicit expected-remote
lease. Stop on input mismatch, remote divergence, refusal, or uncertainty;
report it without retrying or bypassing permissions or review. The orchestrator
resolves the cause and provides a new reviewed handoff when needed.

Publish only the reviewed commit and supplied title/description, using the
[publication requirements](pull-requests.md#publication-requirements). The
publisher does not commit, edit code or content, review, merge, comment, or
recursively delegate. Return the PR URL, observed published SHA, CI status for
that SHA (including pending or unknown), and blockers. A different published SHA
is a blocker; do not report publication complete until the exact reviewed head
is confirmed. This report does not establish acceptance or passing CI; the
orchestrator assesses it under the existing final-head merge gate.

## Published branch rewrites

Before starting a rebase of an already-published branch, inspect the remote
branch and record its commit ID. Verify that this is the
published head whose work the rewrite will replace; reconcile unexpected remote
commits before starting. Keep this expected ID through the rewrite and use it
in an explicit lease when publishing, for example:

```sh
git push --force-with-lease=refs/heads/<branch>:<expected-remote-oid> origin HEAD:refs/heads/<branch>
```

If the remote branch no longer points to that expected commit, the push must
fail. Inspect and reconcile the new remote work before rewriting and publishing
again; do not refresh the expected ID just to make the push succeed or replace
the lease with an unconditional force push. The assigning orchestrator owns
independent review under
[orchestrator handoffs](orchestrator.md#review-and-return); the publisher
follows the
[publication requirements](pull-requests.md#publication-requirements) for CI
reporting and the final-head gate.
