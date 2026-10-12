# Validate Mermaid source from stdin

Use the accepted [backend setup](../../README.md#delivery-map). Deliver one
small Python stdin validator under `script/` for rumdl to invoke. Read all
stdin, force `mermaidx.render(source, backend="quickjs").svg()` and discard the
result. Success exits 0 with no SVG/stdout; failed rendering exits 1 and exposes
its useful reason on stderr. Do not save diagrams or intermediate files.

This leaf owns only adapting stdin to the prepared API. rumdl owns discovery,
fence extraction, process timeout and Markdown diagnostics; the following
[Make/config leaf](../make/README.md) owns its invocation. No parser, process
framework, custom failure categories or direct Markdown dependency is needed.
Do not alter the accepted backend selection or existing backend smoke test.

- **AC-1 DONE** Given valid and invalid raw Mermaid on stdin, the actual
  validator forces QuickJS rendering: valid source succeeds without output,
  invalid source exits 1 with useful backend stderr, and input/checkout files
  remain unchanged.

  Validation: criterion-marked bounded subprocess integration tests invoke the
  actual validator with small valid and malformed inputs using the prepared
  backend. Assert exit 0 for success and 1 for failure, useful backend stderr on
  failure, absent SVG/stdout and unchanged files. Reuse ordinary process helpers
  and existing setup evidence;
  do not test an exhaustive upstream diagram matrix or SVG hashes. Run affected
  lint/type/doc/ac checks under current [testing](../../../../testing.md),
  [integration guidance](../../../../testing-integration.md) and
  [engineering conventions](../../../../engineering.md).
