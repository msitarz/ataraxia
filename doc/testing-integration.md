# Integration tests

Read this file when writing, changing, or reviewing an integration test, after
[testing](testing.md), which owns common rules.

## What an integration test covers

An integration test runs real parts together across a boundary that unit tests
cannot see: a file being read, a process being spawned, or a repository being
changed. Product tests in `test/ataraxia/integration` load strategies from disk
and trade bars through the provider, broker, and compute loop. Tooling tests
exercise our scripts, Make targets, and hooks against real Git and files, under
`test/script/integration` and `test/make/integration`.

Keep pure calculations and state rules in [unit tests](testing-unit.md), and
reserve the shipped command's user-visible flows for
[acceptance tests](testing-acceptance.md).

## Test the product across its boundaries

Keep the participating product components real: strategy loading, provider,
broker, and compute loop. An injected double must not replace the interaction
this test claims to prove; use the
[common boundary policy](testing.md#choose-the-boundary-and-doubles).

Use real strategy and shard inputs under the
[test data guidance](testing.md#treat-test-data-as-data). For non-obvious
trading results, identify the relevant bars and explain the expected profit by
hand. For invalid inputs, check contextual errors, offending paths, and relevant
resource or output state.

## Test tooling in a disposable environment

Copy the minimum checkout into `tmp_path`, or create a repository there with
`git init`. Exercise the actual script, Make target, or hook against that
arrangement.

For external operations that must not run, such as network access or installs,
use a fake executable on `PATH`. The code under test still makes a real
subprocess call, exercising quoting, environment handling, and exit-status
handling. Pass an explicit environment dictionary to child processes; use
scoped `monkeypatch.setenv` when the code under test reads the current process's
environment.

Keep substantial shim source in a real fixture file. For example, a shared
fixture can copy an argument-logging executable before making it discoverable:

```python
@pytest.fixture
def fake_uv(tmp_path, monkeypatch):
    script = tmp_path / "uv"
    shutil.copyfile(ROOT / "test/script/fixtures/registry_uv.py", script)
    script.chmod(0o755)
    monkeypatch.setenv("UV_PROXY_MODE", "record")
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    return tmp_path / "argv.json"
```

The example assumes `ROOT` identifies the checkout and the module imports `os`,
`shutil`, and `pytest`. The existing
[`registry_uv.py`](../test/script/fixtures/registry_uv.py) fixture records
arguments in `argv.json` in the child's working directory; run the child in
`tmp_path`.

- A shim proves only the effects it observes, such as argument routing or error
  propagation. It does not establish that the replaced tool really installs
  packages or avoids network access. Name tests for the property proved.
- For refusal paths, snapshot relevant refs, worktree registrations, or file
  contents before the action and compare the state afterward.
- Where data reaches a shell, include hostile paths, branch names, or commit
  messages. Assert an independent effect, such as a marker file that must never
  appear, rather than only matching diagnostic text.
- Prefer the promised property over a full command transcript unless exact
  arguments are themselves the contract.

## Required tools and evidence limits

If a test requires a real external tool such as Git or Make, require it or skip
with a stated reason. Report unexpected skips as evidence gaps; a skipped test
has not verified its behavior.

For upstream-adoption probes, follow [test ownership](test-ownership.md).
A regression test can exercise our boundary, such as `make doc-check` rejecting
a broken local link, without owning tests of every upstream Markdown rule.

## Patterns in existing tests

These references demonstrate the named qualities, not full compliance with
all current guidance:

- [`test_worktree_cleanup.py`](../test/make/integration/test_worktree_cleanup.py)
  uses real Git in disposable repositories and compares state around refusals.
- `test_backtest_shard` in
  [`test_backtest.py`](../test/ataraxia/integration/test_backtest.py) runs a
  real strategy and shard and compares the complete result. Other tests in that
  file patch internals, and its strategy setup generates source; do not copy
  those patterns.
