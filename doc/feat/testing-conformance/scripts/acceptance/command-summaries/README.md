# Acceptance command summaries

After command construction, extract the remaining five cases from legacy
`test_acceptance_tests.py`: missing-WORK response, three empty summaries and
one selected summary. Reuse its command-script import setup narrowly; keep
units process-free, with real nested pytest in Make integration. Strictly
include only this cleaned subset and owned helpers. Use public functions and
scoped process state, never internal doubles.

- **AC-1 DONE** Given invocation state or pytest summary text, the script
  reports missing WORK with its defined exit and recognizes empty selections
  without misclassifying output containing a selected test.

  Validation: inspect exact results and restoration; run marked cases, strict
  typing, lint/format and doc/ac checks.
