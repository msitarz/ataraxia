# Final measurements and comparison

After matched baseline delivery, measure frozen final code using its exact
preflighted host/tools/Python, preparation and warm-cache conditions under the
[parent protocol](../README.md#timing-protocol). Add final raw outputs/metadata
and the comparison to the separate parent-owned matched report; leave original
baseline evidence unchanged. No version changes after baseline, test changes,
timing assertions or benchmark framework. Stop/report mismatches and retain
failed/interrupted observations rather than silently replacing runs.

- **AC-1 TODO** Given the frozen matched baseline, one warm-up per selection and
  three alternating full/unmarked final runs support separately reported median
  comparisons and preservation limits, or explicitly inconclusive results when
  matching/successful observations are incomplete.

  Validation: independently compare metadata/revisions/cache conditions, run
  order, monotonic timing and median arithmetic against retained raw outputs;
  review failures/skips/deviations, retained coverage and the complete
  Make-suite outcomes, doc checks and latest-head full CI without a causal
  speedup claim.
