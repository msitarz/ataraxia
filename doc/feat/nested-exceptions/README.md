# Nested exception handling guidance

Deliver concise engineering guidance forbidding nested exception handlers.
The maintainer has removed automatic enforcement from this Work's required
outcome; the delivered investigation and guidance complete its scope.

- DONE The pinned Ruff candidates do not enforce the exact nesting rule. The
  [investigation comparison](https://github.com/msitarz/ataraxia/blob/a0c90fe24cfa430a81b360fa10fd5aa13f8b2029/doc/feat/nested-exceptions/investigate/comparison.md)
  preserves the capability gap and the empty repair inventory at its inspected
  base.
- DONE Guidance adopted in
  [engineering conventions](../../engineering.md#code-style).

The independent [focused exception lint Work](../exception-lint/README.md)
remains planned separately. Its rules cannot enforce this exact nesting ban.
This Work authorizes no lint configuration, checker, dependency, code or test
changes, production repairs, or changes to PR #328.

- **AC-1 DONE** The investigation and concise guidance are independently
  reviewed and integrated, with the nesting rule owned by engineering
  conventions and the automatic enforcement gap stated accurately.

  Validation: review the retained investigation and adoption evidence against
  the delivered engineering guidance. Run `make doc-check` and
  `make ac-check WORK=doc/feat/nested-exceptions/README.md` before completion.
