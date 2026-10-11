# Render fences and report bounded failures

Use the accepted [setup outcome](../../README.md#delivery-map) and depend on
[extraction](../extraction/README.md). Deliver `check_markdown`, typed results
and its CLI through the
[checker boundary](../README.md#proposed-public-boundary). The review question
is whether real backend rendering is bounded and produces correct
aggregate/contextual failures. Do not reimplement extraction or wire Make.

The prepared mermaidx API supplies SVG as a string; `.svg()` forces its lazy
rendering without an output file. Its QuickJS engine waits on a thread future
without a render deadline, so a bounded child is needed to contain stalled
rendering. Reuse that API with a small worker and ordinary subprocess timeout
handling; do not introduce a generalized process/protocol framework.

Return exit 0 for no diagrams/all successful fences, 1 for any diagram failure,
and 2 for setup/input failure. A no-diagram selection succeeds without invoking
or importing the backend. In each bounded Python worker, use the mermaidx Python
API `render(source, backend="quickjs").svg()` with the accepted pinned backend.
Do not invoke the upstream mermaidx CLI. Our checker CLI owns worker execution
and diagnostics; the worker owns the API call and exception adaptation.
Lazy construction, ASCII parsing or mocked rendering cannot establish
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

  Validation: criterion-marked public checker tests use narrow external-process
  doubles for unavailable/timeout cases plus real backend aggregation,
  no-diagram and artifact checks. Every subprocess has a timeout. Run focused
  tests and affected lint/type/doc/ac checks; unrun backend evidence or
  unexplained skips leave the relevant criterion unresolved.

Follow current [testing](../../../../testing.md),
[integration guidance](../../../../testing-integration.md),
[strict typing](../../../../engineering.md#preserve-type-precision) and
[test ownership](../../../../test-ownership.md). Retain tests of our boundary
and concrete compatibility regressions rather than exhaustive upstream probes.
Reuse the prepared backend smoke evidence for setup; new real tests exercise
our extraction/rendering/diagnostic boundary. Add only the process adaptation
and tests necessary for that boundary's timeout and result behavior.
