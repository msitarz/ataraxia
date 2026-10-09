# Compute test conformance

## Delivery map

- **DONE** Dependency arrangements: typed dependency
  nodes/runners before graph and result consumers.
- **TODO** [Source arrangements](sources/README.md): typed integer source/sink
  collaborators and small real-CSV arrangements before consumers.
- **TODO** [Graph and results](results/README.md): graph/order/cycle, catalogs,
  dependency values, complete steps and real simple computation.
- **TODO** [Shared state](sharing/README.md): equivalent dependency identity,
  once-per-bar state and fresh runners across executions.
- **TODO** [Source lifecycle](lifecycle/README.md): retained exhaustion, runner
  failure and explicit generator-close state/exception observations.
- **TODO** [Real resource lifecycle](resources/README.md): actual
  source/provider file closure under compute exhaustion/error/explicit close.
- **TODO** [Dependency binding](binding/README.md): all signature/preparation
  cases and preserved positive/negative static contracts.

Merge this map before implementation; deliver leaves in listed order. Paths
below are relative to `test/ataraxia`. Serialize includes, helpers, legacy
subsets and maps; fixture owners merge before consumers. Every changed test,
helper or executable fixture is precisely annotated and explicitly normal
strict checked. Leave untouched legacy remainders outside adoption claims.
Keep `typecheck/compute_contracts.py` on its existing expectations route.

Preserve all 22 existing graph/loop case instances and their identities/markers.
Use concise slice docstrings and independent complete observations; reviewed
static data needs whole-value equality, not duplicated schema validation. Opaque
equality values may use object; structured collaborator contracts retain their
precision. No Any/casts/ignores to conceal mismatches. The reported baseline
strict probe found 53 diagnostics in the two modules; it is context, not
delivery evidence. No global/script typing, test/script/conftest adoption,
package README, Hypothesis or production repair. Split supporting changes before
exceeding five-minute leaf review rather than expanding a consumer's type
migration.

Each leaf runs focused cases and affected legacy remainders, normal strict
typing, existing type expectations, lint/format and doc/ac checks; latest-head
full CI remains the merge gate.

- **AC-1 TODO** Given delivered leaves, retained graph/result/sharing/binding
  cases and compute lifecycles observe complete independent values, precise
  errors and genuine resource closure, preserving provenance and node/result
  type relationships without broad typing or product doubles.

  Validation: integrate independent child artifact/evidence reviews; run all
  compute modules, complete product suite and both existing type-check routes,
  and require latest-head full CI. Planning/probe results alone verify no
  outcome.
