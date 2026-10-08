# Package README coverage

Give each owned code/test namespace a discoverable README describing implemented
purpose, architecture, direct contents and reusable public API. Current package
coverage is uneven; existing test operational notes must survive the revision.
Scope includes src/ataraxia and compute, script, example and test namespace
packages. Data-only directories need no separate README; describe their data
and executable fixtures at the nearest owning README.

- **TODO** [Lasting package documentation guidance](guidance/README.md).
- **TODO** [Recent script test packages](script-tests/README.md).
- **TODO** [Make test packages](make-tests/README.md).
- **TODO** [Product packages](product/README.md).
- **TODO** [Repository scripts](scripts/README.md).
- **TODO** [Product test packages](product-tests/README.md).
- **TODO** [Examples and final navigation](examples-navigation/README.md).

Execute in listed order; serialize edits to shared READMEs. Guidance is a leaf.
The other children are planning subtrees: their proposed delivery slices must
become concrete, independently reviewed and merged leaf contracts before any
package edits. Assess each complete delivery against the five-minute boundary
and split further when needed. This initial map changes no package README,
guidance, runtime behavior, tooling policy or inventory checker/generator.

The approved convention is a compact purpose/architecture explanation with
Mermaid, links to every direct owned module/subpackage with one or two
sentences, and one sentence per reusable public function/class/protocol/type
alias/data structure; describe classes' main operations. Determine actual public
API from exports, callers and fixtures, not imported third-party names or
signature copies. Link reexports to their owning module; subpackage detail
belongs in its own README. Test case modules get summaries, while reusable
helpers, fixtures and types get API descriptions without per-test-function
inventories. Preserve commands/operational notes, link authoritative contracts,
describe implemented behavior only and maintain affected documentation in the
same change as code.

Future delivery validation combines manual architecture/module/API/navigation
review, Mermaid rendering where available, doc-format/doc-check/ac through Make
and latest-head full CI. Rendering limitations must be stated, not counted as
observed rendering. Reuse authoritative guidance rather than copying policies.

- **AC-1 TODO** Readers can navigate all scoped packages and their direct owned
  contents, understand implemented relationships and reusable APIs, and find
  authoritative contracts and preserved operational instructions consistently.

  Validation: Independently compare final READMEs with current exports/callers,
  fixtures and filesystem contents; review architecture/API accuracy,
  cross-links and same-change upkeep guidance. Reuse child review, render
  Mermaid where available and run existing doc/ac checks and latest full CI; no
  new checker.
