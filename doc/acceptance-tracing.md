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
criterion text in the test docstring. Collect matching tests without running
them:

```sh
uv run pytest --collect-only -q \
  -m "covers(work='doc/feat/example/README.md', ac='AC-8')"
```

Remove `--collect-only` to run the selected tests. Use pytest and existing
targeted-test tooling; do not introduce Gherkin, another runner, or a custom
selection plugin.
