# 18. Supervise process workers for shard timeouts

Date: 2026-09-28

## Status

Accepted

Amends [6. Massive parallelism via sharding](0006-massive-parallelism-via-sharding.md).
Shard independence and aggregation from ADR 6 still apply.

Implementation scope and approval evidence live in the
[parallel execution feat slice](../feat/parallel-execution.md).

## Context

Backtesting currently processes shards sequentially. Local parallel execution
must let the main process stop a stuck worker and replace it without interrupting
other assignments. The earlier subinterpreter roadmap idea cannot provide that
isolation and termination guarantee.

Python's executor timeout limits how long the caller waits; it does not stop a
running task. Cancellation cannot cancel running interpreter work, and shutdown
can wait indefinitely. `ProcessPoolExecutor` also lacks a public operation to
kill and replace one assigned worker: `kill_workers()` shuts down the pool, and
abrupt worker death breaks it. The slice's
[bounded probes](../feat/parallel-execution.md#verification-evidence-and-remaining-risks)
confirmed these limitations on Python 3.14.7.

## Decision

Use a bounded pool of individually supervised `multiprocessing.Process` workers
for local parallel execution, using the explicit `spawn` context and public
process APIs. The main process owns assignments, deadlines, termination,
replacement, and shutdown. Each worker executes one shard assignment at a time
and constructs its computation state locally.

Own communication independently for each worker so killing one cannot corrupt
another's channel. Supervision must remain responsive during result transfer.
Kill and reap the affected worker on its deadline, discard its channel, and
replace it for pending work without interrupting other assignments. Cleanup
waits must be bounded. Owning this lifecycle provides the individual termination
and replacement that the executor APIs cannot supply.

Keep supervision in the backtest application layer. Computation remains
independent of processes and concrete I/O; normal resource ownership remains
under [ADR 16](0016-source-manages-its-own-provider-lifecycle.md).
The slice owns deadline parameters, assignment rules, outcome representations,
and CLI behavior; those details are not additional decisions in this ADR.

## Consequences

Process startup and serialization add cost, and Ataraxia must maintain a small
supervisor instead of delegating its lifecycle to an executor. No speedup is
claimed before measurement. Forced termination cannot run Python cleanup;
resource release relies on OS process cleanup. The slice defines the supported
containment boundary and validation for this guarantee.
