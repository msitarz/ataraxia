# Acceptance traceability

Give acceptance criteria stable IDs scoped to their owning README or spec.
During execution, a registered `pytest.mark.covers` marker identifies the Work
and AC ID, and the test docstring includes the covered AC text. State
non-pytest verification in the PR. Check that each active AC has evidence and
that markers for active Works refer to existing criteria.

When a delivery PR removes a Work directory, check its deleted contract
against the tests and other evidence in that PR. After merge, keep the markers
and test docstrings as durable behavior records. A marker for a removed Work is
historical, not dangling: local Git history maps its ID to the original AC.
Do not introduce Gherkin or another test runner.
