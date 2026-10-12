# Integrate Mermaid validation through rumdl

Use the accepted [setup outcome](../README.md#delivery-map). Pinned rumdl 0.2.78
already supplies fence discovery, stdin extraction, tool execution, timeouts and
file/fence diagnostics. The remaining repository boundary is scoped Make/config
integration around the delivered stdin renderer, outside `src/ataraxia`.

## Delivery map

- **DONE** Added `script/validate_mermaid.py` to force QuickJS SVG rendering
  from stdin and expose failure without saving output; its public-process tests
  cover valid and malformed source.
- **TODO** [Make and rumdl configuration](make/README.md): append scoped
  uncached fence validation to existing `doc-check` using the delivered
  validator.

Merge this revised plan before implementation. Deliver the validator first,
then Make/config wiring; sequence shared parent-map edits. Each leaf targets
about five-minute review, including incremental boundary tests. Reuse native
rumdl behavior and ordinary subprocess test helpers rather than adding parser,
fence records, diagnostic models or process machinery. No direct
`markdown-it-py` dependency is required. Preserve the existing backend smoke.

## Native boundary and limitation

rumdl owns Markdown selection/extraction and native execution/error policy.
Our validator reads stdin and calls
`mermaidx.render(source, backend="quickjs").svg()`, discarding the SVG string.
Lazy construction alone does not establish validity. rumdl supplies the
30-second tool deadline and anchors failures to the Markdown file/fence; useful
backend errors pass through stderr. There is no repository-owned aggregation,
category taxonomy or diagram-line mapping requirement.

The pinned-wheel probe exercised backtick, tilde and list-container fences with
the actual renderer. It also found blockquoted fence content still prefixed by
`>`; valid quoted Mermaid can consequently fail. Accept that native limitation
for this bounded adoption. Do not strip `>` globally or add a local extractor
workaround. The separate [upstream report](../upstream-report/README.md) is
nonblocking and can wait; its completion is not an implementation prerequisite.

- **AC-1 TODO** Given the accepted validator and Make/config deliveries,
  `doc-check` preserves existing Markdown/link checks and reaches selected
  Mermaid validation offline with no SVG output, using rumdl's native fence,
  timeout and failure behavior subject to the documented blockquote limitation.

  Validation: independently review child evidence and the integrated
  Make/config/validator boundary; run focused integration tests and doc/ac
  checks. No exhaustive upstream Markdown/parser or timeout suite is required.
