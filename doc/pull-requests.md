# Pull requests

Read when publishing or updating a PR, writing its description, or interpreting
its review state and merge authority.

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
review the final PR head and require its full CI result before merge
consideration, following the [orchestrator handoffs](orchestrator.md) and
[validation policy](validation.md).

## Descriptions

Explain the problem and resulting behavior for a reviewer who has not seen the
conversation. Lead with the concrete change; use a trigger and before/after
example when helpful. Keep the description concise and proportional to the
change. When scope changes, update the title and description to describe the
final implementation, omitting abandoned approaches unless they explain a
relevant tradeoff.

Include validation results and material limitations that help assess the
change, following the [validation policy](validation.md). Link to detailed
scope and evidence in their source records rather than copying them into the
description. PRs carry review discussion and rationale; merged PRs and recorded
approvals provide durable decisions across sessions.

## Review and merge

Draft means changes are complete and await orchestrator review. Once independent
review and any correction loop pass, the owning orchestrator marks the PR ready.
Ready means agent review passed and maintainer review is requested; it does not
mean maintainer approval, merge, or successful CI. Follow
[orchestrator handoffs](orchestrator.md#review-and-return) for the review scope
and human review effort assessment before marking ready.

Repository merge settings do not replace human review or maintainer authority.
The maintainer reviews the current PR revision and performs the merge. Agents
must not merge autonomously; an agent may merge only with explicit maintainer
instruction. Do not change repository settings, use an admin override, or
bypass review or CI requirements.
