# Unit tests

Read this file when writing, changing, or reviewing a unit test, after
[testing](testing.md), which owns the rules common to every test.

## What a unit test covers

A unit test exercises one function, class, or compute node through its public
interface and checks its behavior apart from the rest of the system. Use the
[common boundary and double policy](testing.md#choose-the-boundary-and-doubles)
to isolate collaborators without replacing the behavior under test.

Product unit tests live in `test/ataraxia/unit` and mirror `src/ataraxia`, so
the tests for `src/ataraxia/compute/loop.py` are in
[`test/ataraxia/unit/compute/test_loop.py`](../test/ataraxia/unit/compute/test_loop.py).
Tests for the strategies under `example/` follow the same rules and run through
the example targets in the [Makefile](../Makefile).

Script unit tests live in `test/script/unit`.

## Keep it fast and local

Keep unit tests fast and within one process. They start no subprocess and need
no Git repository. Filesystem input is appropriate when reading files is the
unit's responsibility. If the arrangement requires a process or repository,
use an integration test.

## Test rules as tables of cases

For calculations and state rules (indicators, `Bar`, `Position`, the broker),
the arrangement is a handful of values and the oracle is a literal. Write the
cases as a parametrized table with sentence `ids`, so the table reads as the
specification:

```python
@pytest.mark.parametrize(
    ("value", "inside"),
    [(9, False), (10, True), (15, True), (20, True), (21, False)],
    ids=["below-low", "at-low", "between", "at-high", "above-high"],
)
def test_a_value_is_within_a_bar_only_between_its_low_and_high(value, inside):
    # Given
    bar = Bar(timestamp=1, open=12, high=20, low=10, close=15, volume=1)

    # When
    result = bar.within(value)

    # Then
    assert result is inside
```

A good table covers:

- both sides of each boundary and the equal value, as above
- cold start, warm-up, and empty input
- events that compete within one step, such as a stop and a target in the same
  bar, and gaps that skip a level
- both sides of the market, since buy and sell mirror each other and rarely
  share a bug
- invalid input, with the exact error type and the reason

## Test compute nodes and lifecycles

Build the smallest graph from hand-written nodes that append what happens to a
list, run it, and assert the whole list. For anything with a lifecycle (sources,
sinks, providers), assert the observable state on every exit path: the stream is
exhausted, a runner raises, or the generator is closed early. Check that the
resource ended closed and that the error reached the caller, not that a cleanup
function was called.

## Cover required behaviors

For relevant changes, cover:

- dependency sharing and runner state across equivalent nodes
- provider cleanup on exhaustion, on error, and on explicit generator closure
- rolling-window ordering and warm-up
- broker timing that prevents same-bar exits for new positions

## Test command-line handling up to the first real work

Unit tests of the CLI cover argument parsing, validation messages, and exit
codes up to the point where work would start. A fixture sets `sys.argv`, and
`capsys` reads the output. A test that has to run a backtest, or that patches
`backtest_dir` to avoid running one, is not a unit test. Move it to the
[integration tests](testing-integration.md) with real inputs, and leave the
user-visible flow to the [acceptance tests](testing-acceptance.md).

## Patterns in existing tests

These references demonstrate the named qualities; other details may predate
the common guidance.

- [`test/ataraxia/unit/test_broker.py`](../test/ataraxia/unit/test_broker.py)
  states literal expectations and covers gaps and both-orders-hit boundaries.
- The `test_compute_closes_source_*` tests in
  [`test/ataraxia/unit/compute/test_loop.py`](../test/ataraxia/unit/compute/test_loop.py)
  use hand-written nodes and assert lifecycle state on exhaustion, error, and
  close.
- `test_bar_provider_rejects_malformed_rows_and_closes` in
  [`test/ataraxia/unit/test_provider.py`](../test/ataraxia/unit/test_provider.py)
  uses a real file in `tmp_path` and asserts the error type, message, path,
  cause, and that the file closed.
