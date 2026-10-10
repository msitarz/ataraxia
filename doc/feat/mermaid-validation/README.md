# Investigate Markdown Mermaid validation

Investigate a bounded way to catch fenced Markdown Mermaid failures through
the existing `make doc-check` route. This Work defines an investigation, not
checker adoption, dependencies or implementation. Keep it independent of the
[Work-tree delivery contracts](../work-tree-delivery/README.md).

## Delivery map

- **DONE** Validator investigation: complete-source QuickJS enables exercised
  mermaidx SVG rendering on Python 3.14/macOS x86_64. Defer adoption pending
  setup/platform and diagnostic requirements; GitHub parity remains unverified.
  The
  [retained report](https://github.com/msitarz/ataraxia/blob/15535a9c66c5b1ccdabb745461d0a2f43dd901c2/doc/feat/mermaid-validation/investigation/report.md)
  preserves source/build evidence, probe outcomes and the proposed next
  contract.

The complete investigation artifact and supporting probes target about
five-minute review. Any expanded investigation or adoption needs a concrete
reviewed contract before implementation. Do not rename the route to
`check-doc` or change tools, CI or guidance in this delivery.

- **AC-1 TODO** Given exercised candidate tools and representative Markdown,
  an independently reviewed recommendation identifies a suitable bounded
  `doc-check` integration or explains why none is justified, with reproducible
  evidence, compatibility limitations and a proposed adoption scope.

  Validation: independently review the investigation outcome, recorded versions
  and probe evidence, recommendation and limitations; run doc/ac checks.
