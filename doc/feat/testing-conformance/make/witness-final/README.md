# Witness-final Evaluation

After the [delivered witness correction](../README.md#delivery-map) merges,
freeze its exact merged SHA before preparation in a separate detached input at
`/private/tmp/ataraxia-measurement-witness-final-input`. Preserve all three
earlier inputs unchanged. Follow the
[parent protocol](../README.md#witness-final-attempt) and
[evaluation guidance](../../../../evaluation.md); no test/tool changes or
measurements before correction merge.

Precheck retained baseline host/top-level tools, Python 3.14.6, packages, lock
and selections; disclose intentional fixture Git PATH difference and new copied
post-batch cache preparation/limits. Unrelated drift stops; never silently
refresh baseline. New budget is exactly eight invocations: two warm-ups and six
alternating measured runs, 180 seconds each, no automatic extras. Retain raw
observations at parent-owned witness-final paths; append report without changing
earlier bytes. Different counts/workloads and fixture environments limit
preservation/performance conclusions; no causal/general speedup claim.

- **AC-1 TODO** Given the corrected frozen revision and retained baseline,
  successful matched observations support separate selection medians and
  preservation limits, or retained failures, drift or incomplete observations
  produce an explicitly inconclusive report.

  Validation: independently review frozen provenance,
  preflight/preparation/cache limits, intentional fixture Git difference,
  budget/order, raw outcomes and median arithmetic; assess complete Make-suite
  outcomes, counts/workloads, preservation limits, doc/ac checks and latest-head
  full CI.
