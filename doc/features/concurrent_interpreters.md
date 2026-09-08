# Parallel Shard Processing with Concurrent Interpreters

## Status and Purpose

Feature slice for the v0.2 local parallelization milestone. This document
records the scope, execution contract, and validation results.

Allow a local backtest to process independent shards across CPU cores using Python
3.14 interpreters. Preserve sequential bar processing within each shard, existing
broker accounting, and the CLI result format. This advances
[ADR 0006](../adr/0006-massive-parallelism-via-sharding.md) and the local execution
direction in [ADR 0015](../adr/0015-fork-and-deploy-model.md).

## Starting Point

Before this slice, `src/ataraxia/backtest.py::backtest_dir()` iterated directory
entries sequentially and returned a tuple of results without sorting or filtering.
`backtest_shard()` imports the strategy file, constructs its provider and graph,
consumes the compute loop, and returns the final sink or consumer value.

The CLI aggregates broker accounts and writes JSON only after all shards finish.
Broker results contain package-defined dataclasses; direct Python callers can also
receive primitive sink values, as covered by integration tests.

## Interface and Scope

Add a keyword-only `workers: int = 1` parameter to `backtest_dir()` and a matching
CLI `--workers` positive-integer option. Reject zero and negative values before
starting work. Default to sequential execution for compatibility and debugging;
values greater than one enable an interpreter pool. Cap the pool size at the
number of discovered shards. An empty directory returns `()` without creating a
pool; the CLI retains its existing empty-result error.

Usage:

```sh
uv run ataraxia --sink example/crossover.py --shards-dir sample \
  --workers 4 --output results.json
```

Snapshot directory entries once and sort by filename in both execution modes.
Preserve the current entry-selection behavior in this slice; CSV filtering and
recursive discovery are separate work. Sorting intentionally makes output order
deterministic. Return results in that order regardless of completion order.

## Execution Design

Use `concurrent.futures.InterpreterPoolExecutor`, Python 3.14's high-level pool
interface for multiple interpreters. Each worker uses its own interpreter and GIL,
enabling CPU parallelism. Callables, arguments, and results cross the boundary via
pickle. See the [Python executor documentation](https://docs.python.org/3.14/library/concurrent.futures.html#interpreterpoolexecutor).
Direct interpreter and queue management through
[`concurrent.interpreters`](https://docs.python.org/3.14/library/concurrent.interpreters.html)
is unnecessary for this slice.

1. The coordinator resolves strategy and shard paths to absolute paths and assigns
   each shard an output index.
2. Submit the importable, module-level `backtest_shard()` callable with path strings.
   Keep at most the effective worker count of futures outstanding, replenishing
   as work completes.
3. Each task loads its strategy and constructs fresh provider, graph, runners, and
   broker state. Keep open files, graph objects, and compute history inside the
   worker.
4. The coordinator stores results by index and returns the completed tuple. Only
   the main interpreter aggregates accounts and writes the output file.

Package-defined `Account`, `Position`, and `Bar` values and primitive sink results
must survive serialization without schema changes. Objects defined only in a
dynamically loaded strategy module may not be importable during unpickling; such
custom results require importable definitions or serializable built-in values.
Report serialization failures without silently switching execution modes.

Workers are reused. Fresh graph construction does not clear imported helper-module
globals between tasks. Strategies must keep shard state in runners and providers,
avoid mutable module-global state, and use dependencies compatible with multiple
interpreters. Interpreter isolation is not a security sandbox.

## Failure and Resource Behavior

On an observed task failure, stop submitting shards, cancel work that has not
started, and shut down the pool. Raise an orchestration error identifying the
strategy and shard, chaining the worker or serialization exception. Report pool
initialization failures with execution context. Do not return partial success or
retry shards automatically.

Cancellation cannot stop running tasks; shutdown may wait for them. Apply the same
cleanup on interruption. These limits follow the
[executor shutdown contract](https://docs.python.org/3.14/library/concurrent.futures.html#concurrent.futures.Executor.shutdown).
Do not create or overwrite the CLI output when processing fails.

Outstanding-task limits bound scheduling overhead, not total memory. Each active
shard currently materializes all compute steps, and the coordinator retains final
results. Document this when recommending worker counts.

## Implementation Breakdown

1. Add worker validation, deterministic discovery, and bounded scheduling in
   `backtest.py`, retaining the direct sequential path.
2. Add CLI argument handling and contextual errors; preserve successful output.
3. Add unit tests for validation, ordering, empty input, scheduling limits, and
   failure cleanup. Use mocks only for coordinator behavior.
4. Add real interpreter integration tests and CLI acceptance coverage, then update
   the README and architecture document to describe the implemented behavior.

## Acceptance Criteria

- Sequential and parallel sample runs produce identical ordered results, position
  details, serialized JSON, and aggregate PnL (realized 40, unrealized 0).
- Real-pool tests verify multiple worker interpreters, overlapping tasks, primitive
  and broker result serialization, and fresh runner state across reused workers.
- Invalid strategies, malformed shards, and unserializable results fail with useful
  context; CLI failures preserve an existing output file.
- Empty, single-shard, and more-workers-than-shards cases behave as specified.
- `make ci` and `uv run pytest example/test_crossover.py` pass. Verify whether
  coverage collects worker execution; retain meaningful sequential coverage if it
  does not, without lowering the configured 80% threshold.
- Record wall time and peak memory for a representative CPU-heavy workload with
  one, two, and four workers, including startup overhead. Establish useful workload
  sizes; do not impose a timing assertion on shared CI machines.

## Out of Scope

AWS orchestration, retries, artifact hashing or caching, cross-shard positions,
parallel graph nodes, shared-memory transport, forced task termination, automatic
worker tuning, and compute-history streaming. Existing input/output immutability
plans remain separate; this slice does not implement artifact deduplication.
