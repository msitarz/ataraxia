# Draft guide

For local checks, run `make doc-check`. It checks formatting and local links.
To format, `make doc-format ARGS=PATH` selects paths and may rewrite them.

`make doc-check` is read-only. It is the Markdown and link check. The validation
policy has details here:
[validation policy](../../../../../../../validation.md). Full CI is needed
before merge; local docs checks don't replace it.

If you only care about formatting, `make doc-check` checks Markdown formatting.
It also checks local links. The command never edits files, unlike
`make doc-format ARGS=PATH`.
