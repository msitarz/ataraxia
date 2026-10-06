# Matched baseline refresh

Refresh the old-code baseline under the frozen current host/tools/Python and
prepared offline conditions defined in the
[parent protocol](../README.md#timing-protocol). Inventory interpreters and
preflight both conditions before any measured run. Use a separate disposable
checkout at the exact original code revision solely as evaluation input; this
delivery branch starts from current master. Preserve original report/raw
evidence unchanged. Add separately identified baseline observations to the
parent-owned matched report/raw paths; final execution follows only after this
delivery. No test cleanup, tools/version changes, timing assertions or benchmark
framework.

- **AC-1 TODO** Given matching prepared baseline/final environments and frozen
  revisions, one warm-up per selection then three alternating full/unmarked
  baseline runs produce inspectable outputs, metadata and medians, or retained
  stop observations explicitly explain an inconclusive baseline.

  Validation: independently review preflight/version/cache matching, exact old
  revision, protocol order, monotonic boundaries, raw exits/counts/skips and
  median arithmetic; run doc checks and confirm original artifacts unchanged.
