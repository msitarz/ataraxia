# Acceptance declaration reports

Extract only the eight status/method/marker combinations from legacy
`test_acceptance_coverage.py`. Use eight independent arrangements, each with a
literal complete expected report; no generated Python or test-body branching.
Preserve TODO/DONE neutrality. Own a named typed marker-source fixture before
discovery; precisely type/include only this cleaned subset and owned
helpers/fixture, not remaining legacy cases. Reuse parser setup; keep
expectations independent of production.

- **AC-1 TODO** Given either criterion status and independent marker/method
  declarations, reports state exactly what was declared without judging the
  criterion outcome.

  Validation: review eight literal outcomes and fixture ownership; run marked
  cases, strict typing, lint/format and doc/ac checks.
