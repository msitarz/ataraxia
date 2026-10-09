# Investigate Markdown Mermaid validation

Investigate a bounded way to catch fenced Markdown Mermaid failures through
the existing `make doc-check` route. This Work defines an investigation, not
checker adoption, dependencies or implementation. Keep it independent of the
[Work-tree delivery contracts](../work-tree-delivery/README.md).

## Delivery map

- **TODO** [Validator investigation](investigation/README.md): small parser and
  renderer probes, compatibility evidence and a proposed adoption contract.

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
