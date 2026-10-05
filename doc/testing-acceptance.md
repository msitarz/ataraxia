# Acceptance tests

Read this file when writing, changing, or reviewing an acceptance test, after
[testing](testing.md), which owns common rules.

## What an acceptance test covers

An acceptance test checks the promise the shipped command makes to a user. It
runs in a separate process and observes exit status, stdout, stderr, and files
left behind. Acceptance tests live in `test/ataraxia/acceptance`.

Keep them focused on distinct user-visible flows. Variations that only exercise
an internal rule belong in [unit](testing-unit.md) or
[integration tests](testing-integration.md); a new message or preserved-output
outcome may justify a separate acceptance case.

## Run the shipped command

Use the existing invocation, `uv run --no-sync ataraxia`, through a process
helper. Import no package internals and replace no product components. Arrange
the child's working directory and environment explicitly, without relying on
incidental developer-shell settings. Inherit the `PATH` needed to locate tools;
set other variables only as required by the flow.

For the sample flow, use the shipped example strategy and sample shards.
Other flows may use small real inputs under `tmp_path`, following the
[common test data guidance](testing.md#treat-test-data-as-data).

## Assert the observable contract

Check each relevant part of the user-visible result:

- Exit status: `0` on success, or the defined failure code.
- Standard output: compare the complete text when it is the promised report.
- Standard error: require empty stderr for ordinary success; on failure, check
  the distinctive reason and offending path where applicable.
- Artifacts: parse output and compare the complete promised value. If ordering
  is unspecified or reshaping makes comparison clearer, normalize actual and
  expected values in a helper without dropping required fields.

Derive expected trades and totals independently from the inputs and explain
which shards and trades produce them. Review golden outputs against the data;
do not regenerate expectations by copying the command's output.

## Test failure flows by retained state

For each distinct failure flow, assert the message and relevant filesystem
state: a previous output file is unchanged, or no output was created.
Parametrized failure rows should carry complete arrangements so the body can
state one action and its outcome without branching on setup flags. Multiple
invalid inputs producing the same observable outcome normally belong in lower
levels rather than multiplying acceptance cases.

Use [acceptance tracing](acceptance-tracing.md) when a test covers a Work
criterion. Acceptance is a test type; it does not itself require a Work marker.

## Pattern in the existing sample test

`test_crossover_sample_cli_run` in
[`test_crossover_sample.py`](../test/ataraxia/acceptance/test_crossover_sample.py)
demonstrates the shipped command, exact stdout, empty stderr, and independent
trade expectations. Its artifact assertions check selected fields rather than
the complete value, and its subprocess plumbing remains in the body. Use the
named strengths without treating it as fully compliant with current guidance.
