# Testing

Read this file when writing, changing, or reviewing tests. It owns common
rules and routes to each test type. [Engineering conventions](engineering.md)
own code style and typing; [check and evidence policy](validation.md) owns
check selection and reporting. Read [test ownership](test-ownership.md) when
reviewing tests for cleanup and [acceptance tracing](acceptance-tracing.md)
when adding or reviewing Work coverage markers.

## Pick the test type

Cover behavior at the smallest test type that can observe it through the
appropriate boundary. A stop-loss fill rule needs only the unit. Loading a
strategy file and trading a shard needs several real components. The shipped
command's exit status, output, and artifacts need its entry point in a separate
process. Keep higher-level tests for behavior that lower levels cannot prove.

| Type | Directory | Exercises | Guidance |
| --- | --- | --- | --- |
| Unit | `test/ataraxia/unit`, `test/script/unit`, `example` | one function, class, or node through its public interface | [Unit tests](testing-unit.md) |
| Integration | `test/ataraxia/integration`, `test/script/integration`, `test/make/integration` | real components or external tools across a boundary | [Integration tests](testing-integration.md) |
| Acceptance | `test/ataraxia/acceptance` | the shipped command as a user runs it | [Acceptance tests](testing-acceptance.md) |

Read the guidance for the type you are writing or reviewing after this file.
Run a focused selection with `make test ARGS=<paths>`; example strategy tests
use the example targets in the [Makefile](../Makefile).

## What a test proves

A test arranges a situation, performs an action, and observes the result. It
must fail when the behavior it names breaks. Coverage shows that code ran,
not that assertions detected incorrect behavior.

For each new test, identify the defect it would detect and explain how its
assertions detect it. Check whether any replacement bypasses the behavior
under test. A test that only verifies its own setup needs redesign.

When confidence is uncertain or the behavior is particularly important,
deliberately demonstrate failure: reproduce the defect or temporarily invert a
comparison or omit an operation, then check that the test fails for its intended
reason. Restore production code before completing the change. This is a focused
verification technique, not a requirement to mutate production for every test.

## Choose the boundary and doubles

Exercise behavior through the narrowest public interface that runs it for real:
arguments and return values, a node's `deps` and `factory`, the command line, or
a Make target. Keep the behavior under test real. If a private helper matters,
exercise it through the public path that uses it.

Use small doubles at designed collaborator boundaries, such as a `Protocol`
for a source or provider, or at external boundaries such as processes, network,
clock, randomness, and the user's home directory. A fake should be simpler than
what it replaces and conform to the collaborator's contract. Prefer a
hand-written fake over an unrestricted `MagicMock`, and a real file in
`tmp_path` over `mock_open` when file behavior matters.

A double may return the value ultimately asserted when the contract is
forwarding or selecting that value. That proves forwarding or selection, not
the computation replaced by the double. Assert interactions only when they are
observable obligations, such as entering a source once and exiting with the
error that stopped the run, rather than internal call counts.

Use pytest's `monkeypatch` for scoped process state such as `sys.argv`, the
working directory, environment variables, `PATH`, and home-directory settings.
For child processes, prefer an explicit environment dictionary. Isolate clock
and randomness through injected collaborators where possible. Every temporary
replacement must be restored when the test ends.

Avoid patching our own modules by dotted name, such as
`patch("ataraxia.backtest.compute")`: it couples tests to the internal call
graph and may bypass the behavior being tested. Prefer an existing dependency
injection point or a real integration test. If internal patching is unavoidable
within the task, explain why, keep the behavior under test real, and use scoped
`unittest.mock.patch` with `autospec=True` or a signature-compatible small
replacement. Do not use an unrestricted mock to conceal contract mismatches. The
type-specific guidance may impose stricter boundaries.

## Keep setup readable

Keep simple, unique arrangements in the test or its module. Extract reusable
fixtures and substantial plumbing, especially subprocess execution and
external-tool setup. Read existing helpers before adding another; an owning
suite's `conftest.py` and `support.py` are appropriate for suite-wide reuse,
while narrower helpers belong with their users. Shared registry arrangements
live under `test/script`, with narrow reuse by the Make suite. Name helpers for
what they provide and avoid hiding behavior in setup.

Repeated setup is a signal to consider sharing it, not a reason to force every
arrangement into a central file. A process helper should set a timeout and
return exit code, stdout, and stderr, with combined output available for
assertion diagnostics.

## Make expectations independent

Expected values come from the contract, not from running or copying the
implementation. Use literals or independently reviewed fixtures. Explain
non-obvious numeric expectations with a hand-derived comment.

```python
def test_a_gap_through_the_stop_fills_at_the_open():
    # Given
    entry = Bar(timestamp=1, open=20, high=30, low=15, close=25, volume=1)
    position = Position(entry_bar=entry, side="buy", stop_loss=10, take_profit=30)
    gap = Bar(timestamp=2, open=5, high=5, low=1, close=2, volume=2)

    # When
    result = position.on_bar(gap)

    # Then
    # Entered at 25. The open (5) is past the stop (10), so the fill
    # is at the open: 5 - 25 = -20, rather than the stop's 10 - 25.
    assert result == {"pnl": -20, "closed": True}
```

- Compare complete values when the complete result is relevant. A type, length,
  property, or text-fragment assertion is appropriate when it establishes the
  named contract; do not use it as a substitute for checking required contents.
- Do not restate the production formula, as in `int(10.25 * 4)`. Assert the
  specified value or property. For tooling, assert the promised effect rather
  than reproducing the command transcript unless exact arguments are the
  contract.
- Assert failures precisely: exception type, `match=` on the reason, and
  `__cause__` when preservation is part of the contract. Assert the defined
  process exit code rather than only `!= 0`. Check relevant state left behind,
  such as unchanged files, absent output, or closed resources.
- For human-facing diagnostics, distinctive fragments such as the path and
  reason avoid coupling to incidental wording. Compare exact text when its
  formatting is part of the contract.
- Cover relevant behavioral boundaries, including values on either side and
  equality where it changes the outcome. An interior value cannot distinguish
  `>` from `>=`.

## Shape a test

- Name the behavior: `test_a_dirty_worktree_is_not_removed`, rather than
  `test_worktree_remove_error`.
- Every new or changed test function has `# Given`, `# When`, and `# Then`
  comments separating arrangement, action, and observation, with blank lines
  between phases. Fixture inputs may provide the whole Given phase; say so in
  its comment. Use a separate result assignment when it makes the action clear.
- Exercise one behavior per test. A lifecycle or state-transition behavior may
  require a sequence of actions; do not split away the steps needed to prove it.
- Keep branching and loops out of test bodies where parametrized cases or
  collection assertions express the behavior clearly. Use
  `pytest.mark.parametrize` with descriptive `ids`. Supply complete arrangements
  as case data rather than making the body branch on a flag.
- Around ten statements is a signal to review setup and responsibility. Extract
  cohesive plumbing or separate unrelated behaviors, not code solely to meet a
  count. The statement-count guidance in
  [engineering conventions](engineering.md) also applies to tests.
- Follow [acceptance tracing](acceptance-tracing.md#pytest-markers-and-lookup)
  for `covers` markers and criterion docstrings. Keep descriptions accurate
  about any partial coverage. Otherwise add a docstring only when the name
  cannot explain what the test proves.

## Treat test data as data

Use small builders with defaults when they make relevant input fields easier to
see. Keep substantial source or data inputs, especially strategy modules, as
real files under the owning suite's `fixtures/` directory (currently
`test/script/fixtures/`) and copy them into `tmp_path`. Give variants
names that explain their differences. Avoid assembling source from joined
strings or `.replace` edits that hide it from formatting and static analysis.
Tiny inputs such as a malformed CSV row may be written directly in setup.

For a repository-owned, reviewed static expectation used only for complete
equality, keep the loaded value opaque and compare the complete actual value to
it. A JSON file does not become external or untrusted merely because it is
parsed from disk; do not duplicate its schema or contents solely to satisfy
typing. Complete equality must still detect missing or unexpected fields. Add
only the validation needed for structured consumer access or adaptation,
genuinely external or untrusted input, or a separate validation contract. Keep
meaningful input and output contracts precise, and validate them at their real
boundary.

Write test-created files under `tmp_path` and leave the checkout untouched. If
an external tool requires a repository, copy the minimum it needs there or
create a disposable repository. Do not depend on live network access,
wall-clock timing, uncontrolled randomness, or sleeps. Every subprocess has a
timeout, normally owned by its execution helper.

## Layout, ownership, and adoption

Use pytest, `test_*.py` files, and `test_*` functions. Mirror source modules
inside each test directory where practical. Use fixtures for reusable inputs,
`pytest.raises` for failures, `tmp_path` for filesystem work, and `capsys` for
in-process CLI output. Cover changed behavior and relevant edges; meet the
branch coverage threshold in [pyproject.toml](../pyproject.toml), without
mistaking that floor for proof of quality. Type-contract cases under
`test/ataraxia/typecheck` follow [engineering conventions](engineering.md).

[Test ownership](test-ownership.md) distinguishes retained regression tests
from temporary upstream-adoption probes. Exercise our boundary rather than
only proving that an upstream tool behaves as documented.

Annotate fixture and test parameters, returns, helpers, and collaborators with
precise supported types under
[engineering guidance](engineering.md#preserve-type-precision). As modules are
cleaned up, explicitly extend Pyrefly's configured strict checked set with
passing test modules and their changed helpers or executable fixtures; include
required dependencies within the bounded change. Inclusion of a consumer does
not imply all fixture code or tests are checked. Keep intentional-negative
`test/ataraxia/typecheck` cases separate on the existing `--expectations` route.

Existing tests may predate these rules. The type-specific references illustrate
named strengths, not blanket compliance. Apply this guidance to new or changed
tests; do not rewrite unrelated tests in passing. Follow the
[repair and scope rules](change-rules.md#fix-the-underlying-problem).
