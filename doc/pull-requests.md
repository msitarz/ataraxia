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

Before preparing a rewrite of a published branch, follow the
[expected-remote capture and lease procedure](publisher.md#published-branch-rewrites).
Mechanical execution may use the separate operational publisher after review;
[orchestrator guidance](orchestrator.md#roles-and-delegation) owns its handoff.

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
[publisher](publisher.md).

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
