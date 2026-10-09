# Graph, catalogs and complete results

After source arrangements, own all three cases in `unit/compute/test_graph.py`
and new `unit/compute/test_results.py`, plus their strict includes. Move only
test_prime_catalog, test_computed_node_deps, test_compute_step and test_compute
from legacy test_loop.py. Adopt merged named helpers; leave remaining cases and
fixtures unchanged until their owners migrate them.

Preserve exact A/B graph, B-before-A order and CycleError's reason/cause;
catalog runner values, selected dependency {b:1} excluding the ValueError
sentinel, complete step {B:1,A:4} and source/sink steps 1/8 and 3/10. Exercise
real public graph/loop functions; use independently stated values, with no
production oracle recalculation. Exhaust or explicitly close simple compute
iteration so no live generator is abandoned. Preserve generic keyed lookup and
read-only results.

- **AC-1 TODO** Given retained typed nodes/source, real graph/catalog/step and
  simple computation produce complete literal mappings/order and precise cycle
  failure without dynamic fixture lookup or weakened result typing.

  Validation: review every migrated identity/oracle; run graph/results and
  legacy remainder, plus subtree checks and existing positive/negative
  expectations.
