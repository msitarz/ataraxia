# Equivalent dependencies and fresh execution state

After graph/results, own new `unit/compute/test_sharing.py` and its strict
include. Move test_equivalent_dependencies_share_state_once_per_bar with its
local Total/Branch/Diamond collaborators, precisely typed named runners
replacing untyped lambdas. Use merged source arrangements; no forward graph
framework.

Preserve distinct but equal Total nodes, two branches/offsets10/20, both
executions, literal branch results (11,21)/(14,24), total1/4, five-node steps,
two calls/total4 per runner, stable hashes and distinct runners between
executions. Strengthen selected-field observations into complete relevant
snapshots without aliasing mutable state or deriving expected results from
compute. Keep the two-run sequence that proves fresh state; do not split away
its cross-execution observation.

- **AC-1 DONE** Given equivalent dependency specifications, real compute shares
  state once per bar while preserving complete results/hash identity and fresh
  runner state across both retained executions with precise collaborators.

  Validation: review snapshot independence and retained identities; run this
  module and legacy remainder, plus the subtree's required checks.
