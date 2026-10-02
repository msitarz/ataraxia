# Source facts

1. `make doc-check` checks Markdown formatting and local links without editing
   files.
2. `make doc-format ARGS=PATH` formats selected paths and can edit them.
3. `make doc-check` is local documentation validation, not the full CI gate.
4. The [validation policy](../../../../../../../validation.md) requires full CI
   to pass on the latest reviewed PR head before merge.
