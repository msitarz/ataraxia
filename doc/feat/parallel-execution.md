# Parallel shard execution

Status: proposed. This revision defines the feat slice for specification review;
execution is still sequential.
Tracking: [issue #21](https://github.com/msitarz/ataraxia/issues/21).
PR: [#24](https://github.com/msitarz/ataraxia/pull/24), draft against `master`.
Supervision decision: [ADR 18](../adr/0018-supervise-process-workers-for-shard-timeouts.md),
amending [ADR 6](../adr/0006-massive-parallelism-via-sharding.md).
Terms: [ubiquitous language](../ubiquitous-language.md).
Workflow: [feat slice workflow](../feat-workflow.md).

The issue's completion outcome is the implemented capability described below,
with passing acceptance criteria and required checks. This delivery contains
planning documents only and does not complete issue #21 or validate the future
implementation. Approval evidence and pending work are recorded in the
[handoff](#handoff); general gates follow the linked workflow.

## Problem and current behavior

Independent shards should run concurrently without a stuck strategy preventing
remaining work. The main process must enforce a deadline, preserve shard failure
diagnostics, and replace the affected executor worker.

Code inspected on 2026-09-28:

- `backtest_dir()` iterates `Path.iterdir()` without sorting or filtering, calls
  `backtest_shard()` sequentially, and returns a tuple. Any exception aborts it.
- `backtest_shard()` loads the strategy file, validates `__sink__`, constructs
  `BarProvider` and `SourceNode`, drains `compute()`, and selects the final sink
  or consumer result. It validates that result as `BrokerReturn`.
- `BacktestShardReturn` inherits broker fields and adds absolute paths. It has
  no error variant. Strategy exceptions propagate with their original causes.
- The CLI sums accounts and writes a JSON array only after execution succeeds.
  Acceptance tests require shard failures to leave an existing output untouched.
  There is no pool-size or timeout option.
- `compute()` owns the source context, which delegates to the provider. The
  compute engine has no executor-worker responsibility.

The outcome is a usable local fan-out mode with independently timed assignments,
saved success/error envelopes, and the current successful trading behavior.
Single-process execution remains available by omitting the parallel option.

## Scope and CLI contract

Use `--parallel [N]` to enable a process pool. Without `N`, use
`os.process_cpu_count() or 1`. Explicit `N` must be a positive integer;
`--parallel 1` still runs in a child process with hard deadlines. Omission runs
directly in the main process, without spawning workers.

Use `--shard-timeout SECONDS` for parallel execution, default `5.0`. Require a
finite positive number. An explicitly supplied timeout without `--parallel` is
an argument error: there is no safe hard timeout for arbitrary strategy code in
the main process. Invalid arguments exit with argparse's status 2 before shard
execution or output modification.

```sh
# Existing single-process invocation remains available.
uv run ataraxia --sink example/crossover.py --shards-dir sample --output results.json

# Available processors; default five-second shard deadline.
uv run ataraxia --sink example/crossover.py --shards-dir sample --parallel

# Two workers; configurable deadline in seconds.
uv run ataraxia --sink example/crossover.py --shards-dir sample \
  --parallel 2 --shard-timeout 10 --output results.json
```

Do not sort discovery, dispatch, or results. Preserve directory-entry discovery
behavior in this slice rather than silently introducing an extension filter.
Every discovered entry is an independent assignment; an unreadable entry produces
an error outcome. Compare runs by strategy and shard paths, never array position.
Sequential collection follows discovery; parallel collection follows arrival.

Non-goals: AWS infrastructure, queue delivery/retry behavior, artifact hashing,
immutable storage, multi-source synchronization, per-step artifact persistence,
and process-tree containment for strategies that spawn their own subprocesses.
This slice makes no throughput or memory improvement claim.

## Shard input and outcome contracts

Define a `TypedDict` shard input with `strategy_path: str` and `shard_path: str`,
both absolute. Resolve paths before dispatch. Send no strategy class, sink,
provider, source, runner, open file, or graph across the boundary. The worker
imports the strategy for each assignment and builds fresh computation state.
Successful workers may be reused; imported dependency module globals can remain
warm, as with Lambda. Strategies must not depend on previous shard assignments.

Keep one authoritative shard operation, called directly in sequential mode and
by the worker entry point in parallel mode. It catches ordinary `Exception`s
from strategy import through result validation and produces an error outcome.
Lower-level domain errors and their causes retain their existing contracts.
Do not swallow main-process `KeyboardInterrupt` or `SystemExit`; child process
exit without an outcome is detected by the orchestrator as a worker failure.

`BacktestShardReturn` becomes a union of explicit `TypedDict` variants with
`Literal` discriminators, instead of inheriting `BrokerReturn`:

| Fields shared by both variants | Success | Error |
| --- | --- | --- |
| `strategy_path: str`, `shard_path: str` | `status: Literal["success"]`, `result: BrokerReturn` | `status: Literal["error"]`, `error: ShardError` |

There is no `error` key on success and no `result` key on error. Failed shards
must not contribute a fabricated zero account or partial positions. Broker fields
and their dataclass-to-JSON encoding remain unchanged inside `result`.

`ShardError` is a union of explicit diagnostic records:

- `kind: "exception"`: fully qualified exception `type`, original `message`,
  and formatted `traceback` text. Preserve displayed explicit causes, implicit
  contexts, exception notes, and exception-group contents. Respect Python's
  suppressed-context formatting. Do not pickle live exceptions or traceback
  objects; an exception with unpicklable attributes must still be reportable.
- `kind: "timeout"`: `type` identifying the project's timeout error contract,
  contextual `message`, `timeout_seconds`, `elapsed_seconds`, and
  `traceback: None`. The main process creates it from the assignment record.
- `kind: "worker_failure"`: contextual `type` and `message`, `exit_code: int | None`,
  and `traceback: None` when worker diagnostics are unavailable. Covers unexpected
  exit, startup failure, and invalid or incomplete worker communication.

Exception diagnostics are for logging, not reconstructing and rethrowing arbitrary
strategy exceptions in the parent. Serialization must not turn an original
execution failure into an unrelated pickling error. If diagnostic formatting
itself fails, report that limitation with the original type and available text.

For example, the output array can contain:

```json
[
  {
    "strategy_path": "/work/strategy.py",
    "shard_path": "/work/valid.csv",
    "status": "success",
    "result": {
      "account": {"pnl": 10, "unrealized_pnl": 0},
      "open_positions": [],
      "closed_positions": []
    }
  },
  {
    "strategy_path": "/work/strategy.py",
    "shard_path": "/work/stuck.csv",
    "status": "error",
    "error": {
      "kind": "timeout",
      "type": "ataraxia.errors.ShardTimeoutError",
      "message": "Shard /work/stuck.csv exceeded its 5-second deadline",
      "timeout_seconds": 5.0,
      "elapsed_seconds": 5.01,
      "traceback": null
    }
  }
]
```

## Orchestrator lifecycle and deadline

The main process owns a bounded pool using the explicit multiprocessing `spawn`
context. Assign at most one shard per worker, with at most `N` active assignments.
No worker-local backlog: pending shards stay with the orchestrator and their
deadlines have not started. A failed spawn counts as failure of the assigned
shard, not an unbounded startup retry.

Start the monotonic deadline when dispatch begins, including process startup
when a new worker is needed. Completion requires receiving and validating a
complete outcome before the deadline. This includes strategy import, file reads,
computation, serialization, and transfer. It is a wall-clock limit, not CPU time
or a whole-run deadline. Idle workers have no shard deadline.

Observe all active assignments without blocking on one worker's outcome or
joining one process indefinitely. A large or partial result transfer must not
prevent another deadline being enforced. Give each worker a dedicated channel;
discard the channel when retiring the worker. Do not rely on a shared queue
remaining healthy after a writer is killed.

At expiry, commit one timeout outcome, kill that worker, reap it with bounded
cleanup, close its channel, and replace it if undispatched shards remain.
Unexpected process exit produces one worker-failure outcome with the same
replacement behavior. Never retry the failed shard locally. Unaffected workers
continue; late messages cannot overwrite a committed outcome or be attributed
to a replacement's assignment. An outcome received at or after its deadline is
a timeout. Maintain assignment identity and resolve this race in one parent path.

For a finite set of inputs, repeated worker failure still consumes assignments
and ends the run. If the supervisor cannot clean up a child or maintain its own
invariants, fail the run rather than loop forever or dispatch into that worker.
On exhaustion, interruption, or a parent error, stop dispatching, close channels,
and join or kill all owned children with bounded waits. Do not treat a parent
programming error as an ordinary shard failure.

Resource lifecycle follows [ADR 16](../adr/0016-source-manages-its-own-provider-lifecycle.md)
for normal execution and [ADR 18](../adr/0018-supervise-process-workers-for-shard-timeouts.md)
for forced termination. The timeout applies to the owned worker, not arbitrary
strategy-created descendants.

## CLI output and compatibility

Save every collected outcome, including error diagnostics, into `--output`;
workers never write that shared file. This file is the shard error log as well
as the result artifact. Aggregate only successful nested broker results and
print the existing PnL totals when at least one shard succeeded. Report failure
counts and the output path on stderr. All-success runs retain the current quiet
stderr and exit 0; mixed or all-error runs save outcomes and exit 1. Empty
directories exit 1 and preserve existing output, as today.

This deliberately changes ordinary shard-failure behavior in both modes:
continue processing and replace the previous output with the run's envelopes.
This is the working assumption for preserving errors in the output file;
preserving sequential fail-fast behavior would require a different CLI policy.
Update acceptance tests to assert saved diagnostics and continuation. Preserve
existing output on run-level discovery errors, interruption, or output-writing
failure; use a sibling temporary file and atomic replacement after successful
serialization. A filesystem failure must not be reported as a successful save.

Update Python callers of `backtest_shard()` and `backtest_dir()`, CLI helpers,
example checks, and the installed-wheel smoke test together. Keep existing PnL
units, broker timing, source identity, and rolling-window ordering unchanged.
The output schema is a documented pre-alpha breaking change.

## Existing decisions and boundaries

ADR 18 covers the supervised-worker execution model and amends ADR 6; retain
shard independence and aggregation. The return representation, continuation
policy, and CLI compatibility below are local contracts of this slice, not
separate architectural decisions merely because they change code. No new durable
storage or cloud delivery contract is introduced. There is no existing accepted subinterpreter decision to supersede: it was a README
roadmap item. Amend the roadmap and architecture to reference the chosen process
model and show it as unimplemented until validation.

Reuse ADR 14's `__sink__` loading convention and ADR 12's source/runner identity.
Keep ADR 16's normal provider lifecycle and ADR 17's Tach enforcement. Keep
`BrokerReturn` owned by `broker`; place shard input/outcome contracts and the
supervisor in the backtest application layer. If implementation splits that
layer into modules, declare their dependencies in `tach.toml`; `compute/` still
depends only on its own modules and shared errors.

ADR 7's cloud immutability/idempotency and ADR 15's fork-and-deploy direction
remain applicable and unimplemented. Cloud plans live in
[architecture](../architecture.md#target-execution-and-deployment). A
future adapter resolves cloud artifacts to local paths, then invokes the same
shard operation; local absolute paths alone are not portable cloud references.
No SNS event wrapper or AWS SDK belongs in the local worker contract.

## Delivery steps

After specification approval under the [workflow](../feat-workflow.md), execute:

1. Introduce precise shard input, outcome, and diagnostic types and the shared
   shard operation. Adapt direct sequential callers, aggregation, and JSON
   output together. Verify exceptions and chained diagnostics without processes.
2. Add the supervised pool and dedicated-channel protocol. Verify two concurrent
   assignments, individual deadlines, crash handling, replacement, and cleanup
   with bounded real-process tests. Keep sequential mode working.
3. Wire CLI options and validation. Exercise successful, mixed, timed-out,
   all-error, empty, and invalid-argument runs through the real console command.
   Update CLI help and installed-wheel smoke checks; keep README navigation current.
4. Complete the validation plan below and record evidence here. Follow the
   workflow for reviews and the [contribution procedure](../../CONTRIBUTING.md#make-targets)
   for repository checks.

## Handoff

- Stage: awaiting manual specification review in draft PR #24. No
  implementation is authorized or delivered.
- Defining session: the process pool planning conversation in Codex (this
  conversation). The maintainer can resume it for defining-session review.
- Executor session: not assigned. If the maintainer selects this conversation
  for execution too, record that the roles share a session; do not claim an
  independent review.
- Approved specification commit: none. The instruction to restore the stash
  and adapt the workflow authorizes planning and publication, not execution.
  Record the exact commit and the maintainer's explicit approval before handoff
  to an executor session.
- Branch: `feat/parallel_execution`, reusing the existing owning branch as the
  workflow permits. Base: `master`, including workflow commit `4f6550d`.
- Issue: [#21](https://github.com/msitarz/ataraxia/issues/21); implementation
  outcome remains open during specification-only delivery.
  PR: [#24](https://github.com/msitarz/ataraxia/pull/24), using `Refs #21`.
- Applicable decisions: proposed [ADR 18](../adr/0018-supervise-process-workers-for-shard-timeouts.md)
  and existing ADRs 6, 7, 12, 14, 15, 16, and 17 referenced in this specification.
- Validation: `make ci` passed for this planning revision: 142 repository tests,
  3 example tests, 97.12% branch-inclusive coverage, strict types and expected
  negative cases, architecture checks, installed-wheel smoke test, and audit of
  38 packages. Also checked 63 local Markdown links/anchors, JSON examples,
  whitespace, and the existing branch name. Prior timeout feasibility evidence
  is recorded below; implementation acceptance criteria have not run.
- Unresolved specification finding: the proposal continues after ordinary shard
  errors in both modes and writes error envelopes to `--output`. This intentionally
  changes sequential fail-fast/output-preservation behavior and needs explicit
  acceptance during specification review.
- Reviews: no specification approval or implementation review recorded. Reviews
  must identify their covered commit; later material changes return to the
  specification gate. Once ADR 18 is accepted, add its reciprocal amendment link
  to ADR 6 as required by the ADR workflow.
- Publication: planning baseline `f74cf2d` passed commit hooks and was pushed to
  the owning branch. Draft PR #24 was created against `master`. This handoff/link
  update is part of the specification revision for review; use the current PR
  head commit when recording approval rather than assuming baseline approval.

## Acceptance examples and validation plan

| Preconditions and input | Action | Observable outcome |
| --- | --- | --- |
| Sample strategy and two sample shards | Run without `--parallel`, then with `--parallel 2` | Default mode spawns no workers. Both modes yield identical successful results keyed by paths; realized PnL is 40 ticks and unrealized PnL is 0. Array order is irrelevant. |
| Independent slow and fast valid shards, pool size 2 | Execute both | Both assignments overlap; the fast shard completes while the slow shard is still executing. At most two assignments run concurrently. |
| One nonterminating shard followed by a valid shard, pool size 1 | Run with a short timeout | One timeout envelope; the first PID is dead and reaped; a different PID executes the valid shard. The failed shard is not retried; output contains both outcomes; exit 1. |
| A stuck shard and another active shard, plus pending work, pool size 2 | Reach the stuck shard's deadline | Only its PID is killed. The unrelated assignment completes on its original PID. Replacement executes pending work. |
| More shards than workers | Hold initial assignments and then release one | Pending assignments do not consume their deadline while waiting; their own execution receives the configured limit. |
| Shard strategy raises a chained error with an unpicklable attribute | Execute in either mode | Error file retains type, message, original stack locations, and chaining; later valid shards succeed. No fabricated broker result or pickling failure replaces the error. |
| Child exits abruptly or sends a partial outcome | Execute with pending work | One worker-failure outcome; channel discarded; replacement continues. Other deadlines remain enforceable. |
| Large outcome transfers while another shard hangs | Run with two workers | Result transfer cannot indefinitely block timeout handling; each assignment ends in one valid outcome or its own timeout/error. |
| Malformed CSV, header-only CSV, missing `__sink__`, or import error alongside valid data | Execute in either mode | Contextual error envelopes saved; valid accounts alone contribute to totals; exit 1. All-error runs save errors without printing PnL totals. |
| Pool omitted; explicit timeout supplied, or invalid size/time values (`0`, negative, NaN, infinity) | Parse CLI invocation | Exit 2 before execution; existing output untouched. Bare `--parallel` chooses available processors, falling back to one when unavailable. |
| Deadline/result race with a controlled clock and message arrival | Receive just before, at, or after the deadline | Before succeeds; at/after records timeout. Exactly one outcome, with no late-message reassignment. |
| Empty directory or directory discovery failure | Run CLI with an existing output file | Exit nonzero; existing output unchanged; no owned worker left alive. |
| Interruption or parent failure during active assignments | Stop the run | All owned workers cleaned up with bounded waits; previous output preserved. |
| Serialization or filesystem failure during save | Run with an existing output file | Exit nonzero; previous file intact; no partial replacement or claim that errors were saved. |
| Installed wheel outside the repository | Run copied sample strategy in both modes | Console entry point and spawned imports work without checkout/PYTHONPATH dependencies; nested successful accounts match sample totals. |

Use unit tests with injected clocks/process/channel collaborators for deadline
edges and argument validation. Use integration tests with real spawn workers for
isolation, crashes, termination, and continuation. Give every potentially stuck
integration/CLI test an outer subprocess timeout, and clean up children even on
test failure. Do not use sleeps alone to prove overlap; use explicit handshakes.
Run focused backtest and CLI tests during development. Add positive/negative
Pyrefly expectation cases proving that `status` narrows the envelope and invalid
success/error mixtures are rejected. Follow the
[repository validation procedure](../../CONTRIBUTING.md#make-targets).

## Verification evidence and remaining risks

Quick feasibility verification on 2026-09-28 used the project's Python 3.14.7
and a finite probe under a 12-second outer watchdog; it completed in under three
seconds. An interpreter task slept for 0.8 seconds: `result(timeout=0.05)` raised
while the future was still running; subsequent shutdown waited about 0.845
seconds. A separate context-manager probe also waited for completion after a
result timeout. Startup time contributes to these measurements.

A spawned process sleeping for ten seconds was killed and reaped with exit code
`-9`; an independently spawned replacement completed normally. Calling
`ProcessPoolExecutor.kill_workers()` with two active tasks broke both futures and
prevented further submission. The probe used private pool state only to observe
worker startup, not as a proposed implementation dependency.

These observations agree with the official
[executor documentation](https://docs.python.org/3.14/library/concurrent.futures.html),
[interpreter documentation](https://docs.python.org/3.14/library/concurrent.interpreters.html),
and [process documentation](https://docs.python.org/3.14/library/multiprocessing.html).
They establish the timeout limitation and individual process replacement, not a
validated supervisor or communication protocol. No implementation acceptance
tests have run because implementation has not begun.

Before building the full supervisor, run a bounded experiment with two dedicated
channels: kill one sender mid-transfer while the other completes, then assign
work to a replacement. Success means the unrelated outcome arrives and the
replacement completes within the watchdog. Blocking receive, corrupted unrelated
communication, or leaked children challenges the channel design and must be
resolved before continuing.

Five seconds is an initial default, not a workload-derived budget; expensive
imports and large outputs may need a larger CLI value. Spawn overhead and warm
dependency globals are compatibility risks. Hard kill cannot preserve in-flight
tracebacks or guarantee user cleanup. AWS artifact resolution and duplicate
delivery need separate contracts before cloud implementation.
