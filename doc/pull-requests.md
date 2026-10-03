# Pull requests

Read when publishing or updating a PR or writing its description.

## Publishing

Determine the PR base from explicit task instructions or repository metadata,
following [contribution branch rules](../CONTRIBUTING.md#submitting-a-change).
For Work deliveries with acceptance criteria, follow the
[commit-preservation procedure](acceptance-tracing.md#work-delivery-commits).
The owning orchestrator's responsibilities are defined in
[orchestrator handoffs](orchestrator.md#review-and-return).

Before starting a rebase of an already-published branch, inspect the remote
branch and record its commit ID. Verify that this is the
published head whose work the rewrite will replace; reconcile unexpected remote
commits before starting. Keep this expected ID through the rewrite and use it
in an explicit lease when publishing, for example:

```sh
git push --force-with-lease=refs/heads/<branch>:<expected-remote-oid> origin HEAD:refs/heads/<branch>
```

If the remote branch no longer points to that expected commit, the push must
fail. Inspect and reconcile the new remote work before rewriting and
publishing again; do not refresh the expected ID just to make the push succeed
or replace the lease with an unconditional force push. After publishing,
review the final PR head and require its passing full CI evidence before merge
consideration, following the [orchestrator handoffs](orchestrator.md) and
[check and evidence policy](validation.md).

## Descriptions

Explain the problem and resulting behavior for a reviewer who has not seen the
conversation. Lead with the concrete change; use a trigger and before/after
example when helpful. Keep the description concise and proportional to the
change. When scope changes, update the title and description to describe the
final implementation, omitting abandoned approaches unless they explain a
relevant tradeoff.

Use the [PR description template](../.github/pull_request_template.md) and
remove its instruction comments before publishing. Include material limitations
that help assess the change. Keep evidence prose and check inventories
out of descriptions; evidence remains in commits, CI records, and review
records. Link to detailed scope and evidence in their source records rather than
copying them into the description. PRs carry review discussion and rationale;
merged PRs and recorded approvals provide durable decisions across sessions.
