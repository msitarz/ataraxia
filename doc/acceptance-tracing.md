# Acceptance tracing

Read when assigning Work acceptance-criterion IDs, recording coverage, or
looking up tests by criterion.

## Criteria and coverage

Give each criterion a stable ID such as `AC-1`, unique within its owning Work
README or spec. The repository-relative path to that file scopes the ID. Put
`TODO` or `DONE` beside each criterion, using the same labels as Work maps:

- `TODO` means required test coverage or a stated non-test verification method
  is missing.
- `DONE` means tests are implemented and linked, or the non-test method is
  stated. It does not mean tests passed, review approved, or merge is
  authorized.

## Pytest markers and lookup

Pytest registers the strict `covers` marker in
[`pyproject.toml`](../pyproject.toml). Use keyword arguments to identify the
owning file and criterion:

```python
@pytest.mark.covers(work="doc/feat/example/README.md", ac="AC-8")
def test_inbound_links(): ...
```

Repeat the decorator when a test covers multiple criteria. Include the covered
criterion text in the test docstring.

## Collecting and running selected tests

Use the Make targets to list or run tests for an owning Work file. `WORK` is
required and must be the repository-relative path to its `README.md` or
`spec.md`. Omitting `AC` selects every marked criterion for that Work; setting
it narrows the selection to one criterion:

```sh
make ac-collect WORK=doc/feat/example/README.md
make ac-collect WORK=doc/feat/example/README.md AC=AC-8
make ac-test WORK=doc/feat/example/README.md AC=AC-8
```

`ac-collect` lists selected tests without running them; `ac-test` runs them.
Both return a nonzero status when no tests match. Criteria verified by manual
or other non-test methods remain documented in the Work and are outside these
targets. Use pytest and existing targeted-test tooling; do not introduce
Gherkin, another runner, or a custom selection plugin.
