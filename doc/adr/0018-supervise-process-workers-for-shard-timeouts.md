# 18. Supervise process workers for shard timeouts

Date: 2026-09-28

## Status

Proposed

Amends [6. Massive parallelism via sharding](0006-massive-parallelism-via-sharding.md).
Shard independence and aggregation from ADR 6 still apply.

Implementation is proposed in the [parallel execution feat slice](../feat/parallel-execution.md).
Tracking: [issue #21](https://github.com/msitarz/ataraxia/issues/21).
The complete specification awaits manual review under the
[feat slice workflow](../feat-workflow.md); no execution approval is recorded.

## Context

Backtesting currently processes shards sequentially. The README proposes
`concurrent.interpreters` for local parallelism, but a stuck strategy must not
hold a worker indefinitely. The main process needs to kill that worker, record
the shard timeout, and give another shard to a replacement. Other assignments
must keep running.

Python's [executor API](https://docs.python.org/3.14/library/concurrent.futures.html)
limits how long `Future.result(timeout=...)` waits; it does not stop the task.
Cancellation and shutdown cannot cancel running interpreter work. A bounded
local probe on Python 3.14.7 confirmed that the task continued after a timeout
and executor shutdown waited for completion.

`ProcessPoolExecutor` also lacks a public operation to kill and replace just
one assigned worker. Its `kill_workers()` shuts down the whole pool, and abrupt
worker death breaks it. The probe confirmed both pending results and subsequent
submission failed with `BrokenProcessPool`. See the slice's verification evidence.

The current `BacktestShardReturn` extends `BrokerReturn`. It cannot describe a
failed shard without inventing an account or losing the exception. Failures need
to cross the worker boundary and be saved even when no computation result exists.

## Decision

Use a bounded pool of individually supervised `multiprocessing.Process` workers
for opt-in local parallel execution. Use the explicit `spawn` context and public
process APIs. The main process owns assignments, monotonic deadlines, worker
termination, replacement, and shutdown. Each worker executes one shard at a time.
It receives strategy and shard paths, loads the strategy, and constructs the
provider, source, and graph locally. Workers do not write the CLI output file.

On a shard deadline, kill and reap only its worker, discard its communication
channel, and record one timeout outcome. Start a replacement for remaining work.
Do not retry the timed-out shard. Other workers retain their assignments. Use
independent worker channels; partial messages from a killed process must not
corrupt another worker's channel or block deadline enforcement. Result transfer
is part of the deadline. Cleanup waits must be bounded.

Replace `BacktestShardReturn` inheritance with a discriminated success/error
envelope. Success embeds the unchanged `BrokerReturn`. Errors contain
serializable diagnostics, preserving exception type, message, and traceback
including exception chaining. Capture execution exceptions at the shard boundary,
without rewriting them as generic domain errors. For a killed or crashed worker,
the orchestrator supplies an error record with the available supervisor evidence;
it cannot recover a traceback from that worker.

Use the same shard operation and envelopes for sequential execution in the main
process. Sequential execution remains the default and has no hard deadline.
Both modes continue after ordinary shard failures and save their outcomes. The
CLI aggregates successful accounts and exits nonzero if any shard failed. This
intentionally changes fail-fast behavior and the flattened output schema.

Discover and dispatch shards without sorting. Parallel results are collected as
they arrive, with no ordered-output promise. Graph dependency ordering and bar
ordering inside each shard are unaffected.

Keep orchestration in the backtest application layer and computation independent
of processes and concrete I/O. [ADR 16](0016-source-manages-its-own-provider-lifecycle.md)
still owns provider cleanup during normal execution and Python exceptions. A
forced process kill cannot run Python cleanup; the OS closes its resources.

The path-only input and outcome contract can serve a future Lambda adapter. The
planned cloud fan-out is SNS -> SQS -> Lambda; deployment, artifact resolution,
queue retries, and idempotency are separate work under
[ADR 7](0007-idempotency-and-immutability-of-backtester-runs.md) and
[ADR 15](0015-fork-and-deploy-model.md). Local paths are not cloud artifact IDs.

## Consequences

Process startup and serialization cost more than single-process execution.
Ataraxia owns a small supervisor rather than relying on an executor's lifecycle.
That cost buys individual worker termination and replacement. No speedup is
claimed before measurement.

Callers and saved-result consumers must handle the new envelope and error
records. Successful trading calculations stay unchanged. Hard deadlines require
parallel mode, including a pool of one worker. Strategy-created subprocess trees
and durable partial computation traces are outside this slice.
