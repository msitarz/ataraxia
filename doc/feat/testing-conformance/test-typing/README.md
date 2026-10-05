# Incremental test typing adoption

Normal strict Pyrefly currently includes source and the crossover example,
not ordinary test modules. Seed enforcement with only
`test/ataraxia/unit/test_bar.py`, using the existing `make typecheck` and CI
route. A focused baseline check reports one missing annotation for the `data`
parameter; adoption has not yet fixed or enforced it.

Add that exact module to `project_includes`, retaining existing entries and
`preset = "strict"`. Add minimal precise fixture/test annotations needed to
pass; do not change runtime behavior, assertions, or test structure in this
leaf. Keep intentional-negative `test/ataraxia/typecheck` files on the existing
`--expectations` route, outside normal project inclusion.

This adoption also adds a short lasting test-typing paragraph to
`doc/testing.md`: precise fixture/test parameters and returns, incremental
extension of the configured strict checked set to cleaned modules/helpers, and
separation of intentional-negative expectations. This is a future adoption edit,
not a guidance change in this planning delivery.

This adoption precedes suite cleanup. Later cleanup leaves annotate changed
modules and their fixture/helper contracts, then explicitly add passing modules
to the normal checked set. Annotate fixture inputs/returns, process-result
helpers, parametrized values, and collaborators with precise supported types.
When helpers or executable fixtures need checking, include those concrete files
and required dependencies within the owning bounded leaf; do not imply all
fixture code or tests are checked merely because a consumer is included.

No all-suite diagnostic migration, blanket `Any`, precision-erasing casts or
ignores, disabled diagnostics, source strictness reduction, or behavior cleanup
is included. Follow
[type precision guidance](../../../engineering.md#preserve-type-precision) and
[testing guidance](../../../testing.md). If pilot annotation changes reveal an
independent defect, report it rather than expanding this leaf.

## Acceptance

- **AC-1 TODO** Given the adopted configuration, default `make typecheck` checks
  the Bar pilot alongside existing source/example entries under the strict
  preset; other ordinary test modules are not newly blanket-included.

  Validation: independently inspect inclusion and annotations; run focused
  `make typecheck ARGS=test/ataraxia/unit/test_bar.py` and default
  `make typecheck`; require full CI on the latest reviewed PR head.
- **AC-2 TODO** Given intentional-negative type cases, default type checking
  still checks them through `--expectations`, preserving their expected
  failures.

  Validation: inspect the unchanged Make route and run
  `make typecheck-expectations`; review latest-head CI execution.
- **AC-3 TODO** Given the pilot diff, annotations preserve fixture/value
  precision without behavioral edits, broad escape hatches, or weaker source
  checking; subsequent cleanup has an explicit incremental inclusion obligation.

  Validation: independently review the complete diff against engineering and
  testing guidance; verify the adopted lasting guidance and parent contract
  state the incremental obligation and adoption dependency. Run
  `make test ARGS=test/ataraxia/unit/test_bar.py` to verify unchanged runtime
  behavior. Later cleanup execution and inclusion are assessed by parent AC-5.
