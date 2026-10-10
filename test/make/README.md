# Make tests

Make target tests: `integration/`. Registry arrangements are reused from
`../script/`.

Read [common testing guidance](../../doc/testing.md) and the relevant
test-type guidance linked there.

The `real_tool` marker identifies cases invoking real uv-managed tools,
including nested pytest and missing-tool checks. Fake-uv routing, real-Git-only
cases, and help-only cases remain unmarked. Normal test and CI commands run both
groups. For a fast local selection, run:

```sh
make test ARGS=test/make/integration PYTEST_ADDOPTS='-m "not real_tool"'
```

Pass `PYTEST_ADDOPTS='--collect-only'` as a Make command-line variable after
`make test` to inspect full selection, adding `-m "not real_tool"` for the
filtered selection. `ARGS`
accepts paths only. This filter changes selection, not the coverage obligations
of CI.
