# Acceptance traceability

Give acceptance criteria stable IDs scoped to their owning README or spec.
Link pytest tests with a registered `covers` marker and state non-pytest
verification explicitly. Check for uncovered criteria and dangling test
references without introducing Gherkin or another test runner.
