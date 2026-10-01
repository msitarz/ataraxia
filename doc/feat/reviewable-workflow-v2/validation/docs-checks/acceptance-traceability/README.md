# Acceptance traceability

Give acceptance criteria stable IDs scoped to their owning README or spec.
Track coverage with `TODO` and `DONE` beside each AC, using the same labels as
Work children:

- **TODO:** required tests or a stated non-test verification method are missing.
- **DONE:** tests are implemented and linked, or the documentation/manual
  verification method is stated. This means coverage is supplied, not that
  tests passed, review approved the result, or merging is authorized.

CI gates test results; review assesses whether tests and non-test verification
actually establish the intended behavior. Do not store test-result snapshots,
evidence SHAs, or generated verification summaries in Work READMEs.
The parent remains `TODO` until acceptance and required review gates are met.

## Test lookup

Register `covers` for strict pytest marker checks. Use keyword arguments so
pytest can select tests directly. `work` is the repository-relative path of the
owning README or spec, preserving file-scoped AC identity:

```python
@pytest.mark.covers(work="doc/feat/example/README.md", ac="AC-8")
def test_inbound_links(): ...
```

Repeat the decorator when a test covers multiple ACs. The test docstring
includes the covered AC text. Find matching tests without running them:

```sh
uv run pytest --collect-only -q \
  -m "covers(work='doc/feat/example/README.md', ac='AC-8')"
```

Remove `--collect-only` to run those tests. Use existing targeted-test tooling;
do not introduce Gherkin, another runner, or a custom selection plugin.

## Coverage checks and cleanup

A small checker validates that markers for active contracts refer to existing
ACs and that each `DONE` criterion has test coverage or an explicit non-test
verification method. It does not inspect test results or query CI. Missing
coverage remains `TODO`; document non-test methods beside the relevant AC.

When a temporary probe is removed while its acceptance criterion remains
active, keep that criterion covered by stating the one-time verification method
and linking the delivery PR beside the criterion. The PR records the observed
result and removal rationale. The method is adoption evidence, not continuing
regression coverage, and lets coverage checks find the evidence without marking
the criterion incomplete.

When a delivery PR removes a Work directory, check its deleted contract against
the tests and other verification methods in that PR. Keep markers and docstrings
on retained tests as durable behavior records. A marker for a removed contract
is historical, not dangling: Git history maps its path and ID to the original
AC.
