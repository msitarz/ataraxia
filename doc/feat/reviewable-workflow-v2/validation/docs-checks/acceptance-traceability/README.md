# Acceptance traceability

Give acceptance criteria stable IDs scoped to their owning README or spec.
During execution, a registered `pytest.mark.covers` marker identifies the Work
and AC ID, and the test docstring includes the covered AC text. State
non-pytest verification in the PR. Check that each active AC has evidence and
that markers for active Works refer to existing criteria.

## Partial-progress summary

Generate an AC summary in the active Work README from test markers, recorded
test results, and explicit non-pytest evidence. Do not maintain a second manual
coverage table. Distinguish these facts for each criterion:

- **Covered:** a retained test references the AC; this alone proves neither
  passing behavior nor completion.
- **Verified:** applicable tests or another acceptance check passed for the
  recorded revision. Show the evidence reference and revision; do not present
  results from an earlier revision as current verification.
- **Pending:** required evidence is missing, failing, or needs renewal after
  relevant changes. Identify the outstanding check.

Coverage and verification are separate: an AC can be covered but still pending,
or verified by a non-pytest check without retained test coverage. Generating the
summary must not silently rerun tests or turn missing results into success.
Checks detect a stale generated summary; an explicit update refreshes it.
The parent remains `TODO` until all ACs and required review gates are satisfied.

Preserve verified temporary-probe evidence when tests are intentionally removed
under [Acceptance test lifecycle](../../acceptance-test-lifecycle/README.md).
Report it as historical adoption evidence, without claiming retained coverage
or verification of later changes.

When a delivery PR removes a Work directory, check its deleted contract against
the tests and other evidence in that PR. After merge, keep markers and
docstrings on retained tests as durable behavior records. A marker for a removed
Work is historical, not dangling: local Git history maps its ID to the original
AC. Do not introduce Gherkin or another test runner.
