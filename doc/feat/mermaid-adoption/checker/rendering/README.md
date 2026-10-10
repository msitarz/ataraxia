# Render fences and report bounded failures

Depend on accepted [setup](../../setup/README.md) and
[extraction](../extraction/README.md). Deliver `check_markdown`, typed results
and its CLI through the
[checker boundary](../README.md#proposed-public-boundary). The review question
is whether real backend rendering is bounded and produces correct
aggregate/contextual failures. Do not reimplement extraction or wire Make.

Return exit 0 for no diagrams/all successful fences, 1 for any diagram failure,
and 2 for setup/input failure. A no-diagram selection succeeds without invoking
or importing the backend. Force `.svg()` with the accepted pinned QuickJS
backend; lazy construction, ASCII parsing or mocked rendering cannot establish
validity. Do not persist SVG/intermediate outputs in the checkout.

Each renderer child has a 30-second timeout and is reaped on failure;
sequential execution bounds concurrency to one. Report timeout as render failure
and continue to later fences. Aggregate diagram failures across files. Report
setup/input failures distinctly without relabeling them syntax errors; exit 2
takes precedence if categories are mixed. Diagnostics include path and fence
line, mapped Markdown line when an engine diagram line is available, and
category/reason. Preserve useful parse errors; unsupported/render failures and
opaque wrapper exceptions use fence-level fallback without inventing syntax
classification or source location.

- **AC-1 TODO** Given real pinned backend rendering through our CLI, corrected
  sequence and representative class/state/flowchart fences succeed; malformed
  first/later fences and the original invalid sequence fail with path/fence
  diagnostics and available mapped lines or opaque fallback.

  Validation: criterion-marked real backend integration tests retain fixture
  provenance from the immutable parent report. Assert success/failure and
  contextual diagnostics, not SVG counts/hashes or visual/GitHub parity.
- **AC-2 TODO** Given no diagrams, setup/input failure, multiple diagram
  failures or timeout, defined exit codes/categories and aggregate reporting
  hold, later fences are attempted where setup permits, processes are reaped and
  no checkout artifacts remain.

  Validation: criterion-marked public checker tests use a typed process
  collaborator for unavailable/timeout cases plus real backend aggregation,
  no-diagram and artifact checks. Every subprocess has a timeout. Run focused
  tests and affected lint/type/doc/ac checks; unrun backend evidence or
  unexplained skips leave the relevant criterion unresolved.

Follow current [testing](../../../../testing.md),
[integration guidance](../../../../testing-integration.md),
[strict typing](../../../../engineering.md#preserve-type-precision) and
[test ownership](../../../../test-ownership.md). Retain tests of our boundary
and concrete compatibility regressions rather than exhaustive upstream probes.
