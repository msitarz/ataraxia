# Pull requests

Read when publishing or updating a PR or writing its description.

## Publishing

Determine the PR base from explicit task instructions or repository metadata,
following [contribution branch rules](../CONTRIBUTING.md#submitting-a-change).
For Work deliveries with acceptance criteria, follow the
[commit-preservation procedure](acceptance-tracing.md#work-delivery-commits)
to complete and independently review both commits before publication. Publish
the reviewed sequence once; require full CI on the final reviewed PR head before
merge. A later material correction remains permitted and requires refreshed
acceptance evidence, independent review, and full CI on the corrected head.
The owning orchestrator's publication and description responsibilities are
defined [below](#descriptions).

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
or replace the lease with an unconditional force push. Follow the
[orchestrator handoffs](orchestrator.md) and
[check and evidence policy](validation.md) for review and CI requirements.

## Mechanical publisher

After independently reviewing the exact artifact and description and assessing
acceptance, the orchestrator may delegate push/create/update to the reusable
`publisher` operational subagent, using the maintainer-authorized Luna at medium
effort. This role is distinct from a Work leaf executor; general leaf model
policy is unchanged. The orchestrator retains review, acceptance and final-CI
assessment, publication accountability, and the maintainer handoff.

The handoff names this guidance, the worktree, exact reviewed commit, approved
title and description file, and existing PR when updating. Identify the reviewed
description contents with a digest or an immutable copy so the publisher can
verify the file has not changed. Include explicit repository or base overrides
only when authorized; a rewrite also requires the expected remote commit
recorded before rebase under the lease procedure above.

Resolve the repository, remote branch, and base from repository and existing-PR
metadata unless explicitly overridden, following the contribution branch rules.
Check that metadata agrees, the worktree is clean including untracked files,
HEAD equals the reviewed commit, and title and description match the approved
inputs. Check the remote branch before pushing: ordinary updates must preserve
all remote commits, and rewrites must use the explicit expected-remote lease.
Stop on input mismatch, remote divergence, refusal, or uncertainty; report it
without retrying or bypassing permissions or review. The orchestrator resolves
the cause and provides a new reviewed handoff when needed.

Publish only the reviewed commit and supplied title/description, using the
ready-PR and description rules below. The publisher does not commit, edit code
or content, review, merge, comment, or recursively delegate. Return the PR URL,
observed published SHA, CI status for that SHA (including pending or unknown),
and blockers. A different published SHA is a blocker; do not report publication
complete until the exact reviewed head is confirmed. This report does not
establish acceptance or passing CI; the orchestrator assesses it under the
existing final-head merge gate.

## Descriptions

Explain the problem and resulting behavior for a reviewer who has not seen the
conversation. Lead with the concrete change; use a trigger and before/after
example when helpful. Keep the description concise and proportional to the
change. When scope changes, update the title and description to describe the
final implementation, omitting abandoned approaches unless they explain a
relevant tradeoff.

The executor returns local changes and a concise local result. The owning
orchestrator independently reviews the artifact and completes corrections before
publishing a ready PR or an amendment to an existing PR. After review, the
orchestrator prepares or updates the description from the reviewed artifact and
the executor's concise local result; there is no separate executor PR-writing
phase. Consolidate publication of the reviewed description, allowing later
material corrections. The orchestrator remains accountable for publication of
the Work branch and any rewrite to its PR; mechanical execution may use the
[publisher](#mechanical-publisher).

Do not publish draft PRs. Ready means agent review passed and maintainer review
is requested; it does not mean maintainer approval, merge, or successful CI.
Apply the [decision-record status rule](decision-records.md#record-format) to
ADRs and WDRs before publication. Follow the
[check and evidence policy](validation.md) for mechanical-check
evidence and the latest-head CI gate.

Use the [PR description template](../.github/pull_request_template.md) and
remove its instruction comments before publishing. Write the description to a
temporary Markdown file. From the repository, run
`make doc-format ARGS=/absolute/path/to/pr-description.md` to format it with
the repository's rumdl configuration. Inspect the formatted result and use that
file for PR creation or updates with `gh pr create --body-file` or
`gh pr edit --body-file`. Keep only the template's heading and sections. Include
material limitations that help assess the change.
Do not add evidence links, evidence prose, acceptance criteria, or check
inventories. Do not add PR comments or discussion to record review or report
checks.
