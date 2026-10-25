# Experimental CLI process supervisor

## Purpose

Provide bounded CLI invocation for the engineering-review experiment without
requiring a production reviewer runner.

## Goals

- Run the system `codex exec` command through a small native async
  boundary with truthful output, exit, and completion accounting.
- Request termination of the owned POSIX process group, optionally allow a
  bounded grace period before SIGKILL, await the direct CLI, and stop the
  experiment if cleanup fails.

## Non-Goals

- Deliver a production runner, generic batch scheduler, or concurrency library.
- Implement the full Evaluation caller, trial scheduling, retry policy, budgets,
  scoring, or evidence persistence, which remain owned by the parent Evaluation
  Work.
- Discover arbitrary process trees, contain escaped daemons, classify zombies,
  or sandbox CPU, memory, or process counts.
- Change invocation policy, trial budgets, telemetry accounting, or authorize
  model calls.
- Add elaborate exception aggregation or public options used only by tests.
- Add arbitrary escalation policies, a signal framework, parent-death recovery,
  or a guarantee of graceful completion or orderly output flushing.

## Mechanisms

- Python `asyncio` owns subprocess creation, stream reading, waiting,
  cancellation, and cleanup for one attempt through an awaitable boundary.
- A dedicated POSIX process group scopes termination to the invocation's owned
  group, with immediate SIGKILL by default and an optional
  SIGTERM/grace/SIGKILL path under the same total cleanup budget.
- The Evaluation caller owns dispatch policy, signal handling, and evidence
  accounting; this child delivers the stop hook and representative caller
  boundary verified by AC-3.

## Inherited constraints

The [Evaluation constraints](../README.md#inherited-constraints),
[CLI boundary](../protocol.md#cli-invocation-boundary-and-accepted-limitation),
and [protocol bounds and stop handling](../protocol.md#bounds-and-stop-handling)
apply unchanged except for the Evaluation-scoped process guarantee defined here.
The protocol owns execution and cleanup deadlines, combined-output allowance,
concurrency, and retries; this Work adds no call budget.
The supervisor API permits capture without a byte cap, but the Evaluation
caller must retain the protocol's positive 1 MiB combined-output allowance.

The supervisor verifies its local lifecycle and output guarantees with
disposable processes. The Evaluation owner verifies actual invocation,
dispatch, retained evidence, and all other experiment protections across the
integrated harness; child completion does not establish those guarantees or
production readiness.

## Visuals

The active supervisor module provides one-attempt composition and a narrow
caller stop hook, including retained acquisition/cleanup tasks, cancellation
evidence, and post-termination exit-status forwarding. The native adapter and
disposable process regressions now cover acquisition, output capture,
process-group signaling, and direct-child cleanup. A reusable disposable caller
fixture exercises stop latching, cancellation and signal delivery, unsafe
cleanup accounting, and retry after confirmed cleanup through the public
boundary. This represents the generic call-site pattern and does not verify
the absent Evaluation harness. All child criteria have been reviewed and
accepted within this local scope. The parent Evaluation Work remains TODO,
including actual harness integration under its AC-3.

The [architecture](architecture.md) records native behavior, effect sequence,
and ownership. AC-1 and AC-2 describe the accepted immediate-SIGKILL baseline;
AC-4 is implemented and accepted with focused regressions. The
[typed delta](design/grace-interface.pyi) records the accepted boundary; the
historical reviewed interface remains unchanged.

## Acceptance criteria

### **AC-1 DONE** Async invocation returns bounded, truthful observations

An Evaluation caller can await one command attempt with the existing protocol
limits and receive observed output, exit status when available, termination
reason, and cleanup status through a reviewed typed boundary.

- Execution and cleanup timeouts must be positive and finite, and invalid
  values refuse launch.
- `AttemptRequest.output_limit_bytes` accepts nonnegative integers, with zero
  disabling the output byte cap and positive values capping retained stdout
  and stderr bytes in total.
- Negative output limits refuse launch.
- The supervisor performs no hidden retries.
- Success and nonzero exit retain their actual exit status and observed output;
  unavailable observations stay unavailable.
- With a positive output limit, the retained stdout/stderr prefixes stay within
  the combined allowance, and overflow is visible and terminates the invocation
  rather than silently truncating successful output.
- With a zero output limit, capture has no byte cap and cannot terminate for
  output overflow.
- Cancelled or interrupted attempts retain observed partial prefixes even when
  the output limit is zero.
- Timeout bounds the active invocation even when the CLI leader exits while an
  owned child keeps its output open; a leader's zero exit cannot turn timeout,
  cancellation, or overflow into success.

### **AC-2 DONE** Termination has bounded, accountable cleanup

Success, failure, timeout, cancellation, and overflow request termination of the
owned group through the OS and await/reap the direct CLI within the protocol
cleanup deadline, or explicitly report failure or expiry of that step.

- The CLI launches in a dedicated owned group; the termination request targets
  that group even after leader exit, when children may remain.
- Cleanup status records the OS signaling outcome and direct CLI wait/reaping
  outcome; signal or wait failure, expiry, permission errors, and unknown
  outcomes remain explicit failures, with original failure diagnostics retained.
- The supervisor trusts OS signal/exit semantics and ordinary resource
  reclamation on exit; it does not enumerate group members, probe absence or
  zombies, or prove that every descendant exited.
- No process-tree discovery, whole-host audit, or graceful escalation framework
  is required.
- Task cancellation propagates after bounded cleanup and cannot become a
  retryable `OSError` or successful result.
- Acquisition failure or interruption leaves no unawaited operation that could
  subsequently acquire an unowned subprocess; any uncertainty is reported as
  incomplete cleanup.

### **AC-3 DONE** Stop hook supports a verified representative caller

The supervisor's public stop hook reports cancellation and unsafe cleanup to
its caller. A representative caller verifies stop handling, retry ordering,
and incomplete-run accounting through that boundary.

- `call_supervisor` invokes the caller's stop hook on cancellation or unsafe
  signal/wait cleanup and preserves the attempt's failure and cleanup evidence.
- The representative caller receives `SIGINT` and `SIGTERM`, or task
  cancellation, latches stop before fallible recording, and cleans up the active
  invocation through AC-2 without retry.
- Unsafe cleanup marks that representative run incomplete and prevents later
  dispatch independently of the ordinary infrastructure-failure threshold.
- The representative caller retains active-call evidence and not-started
  accounting, including when recording fails after stop is latched.
- A representative retry starts only after the prior direct CLI is reaped and
  cleanup permits dispatch; the supervisor itself runs exactly one attempt.

Actual Evaluation-harness integration and verification remain owned by
[parent AC-3](../README.md#ac-3-todo-experimental-execution-verifies-its-applicable-guarantees).
These representative checks do not establish that integrated outcome.

### **AC-4 DONE** Optional grace preserves bounded, accountable cleanup

A caller can opt into SIGTERM followed by a bounded grace period and SIGKILL,
while the default preserves immediate SIGKILL and the existing result semantics.
The optional grace path is implemented and accepted under this criterion.

- `AttemptRequest.grace_seconds: float = 0.0` accepts finite nonnegative numbers
  excluding `bool`, strictly less than positive `cleanup_timeout_seconds`;
  invalid construction raises `ValueError` before launch.
- Zero grace sends no SIGTERM and immediately requests SIGKILL for the owned
  group, preserving the current cleanup behavior.
- Positive grace requests SIGTERM for that group after capture ends; only a
  `sent` outcome starts the grace period.
- SIGTERM `failed` or `no_target` skips grace and proceeds directly to SIGKILL.
- During grace, the supervisor drains and discards stdout and stderr so a
  cooperative process can progress without blocked pipes; the captured output
  prefixes are already final and do not grow during cleanup.
- Reaching EOF on both streams does not shorten the requested grace; draining
  continues until the grace or shared cleanup deadline. An unexpected read
  failure settles both readers and proceeds promptly to final SIGKILL, pipe
  closure and the remaining-budget direct-child wait before propagating the
  exact original error with cleanup evidence attached. Cancellation precedence
  remains in force.
- SIGKILL is requested for the owned group after grace, even if the leader has
  exited or the streams reached EOF; leader exit never proves group absence.
- Cleanup computes one absolute deadline using `loop.time()` at cleanup entry;
  signaling, grace, pipe handling, and direct-child waiting share that existing
  total budget, with grace ending no later than that deadline.
- Grace or total-budget expiry still requests final SIGKILL and explicitly
  closes the local output pipes after that request, including when signaling
  fails; no new wait budget is created.
- Direct-child waiting receives only the remaining cleanup budget; if none
  remains, the wait is reported as expired and any observed raw returncode is
  retained without claiming successful reaping from leader exit alone.
- Cleanup evidence records each signal attempt separately in order, including
  signal identity, `sent`/`no_target`/`failed`/`unknown` outcome and its
  diagnostic; zero grace records only SIGKILL, positive grace records SIGTERM
  then SIGKILL.
- Missing or unknown required signal evidence, any failed signal (including
  failed SIGTERM followed by successful SIGKILL), contradictory diagnostics,
  and failed, expired or unknown direct-child wait forbid further dispatch; the
  accepted signal outcomes `sent` and `no_target` plus a reaped direct child
  permit it without proving whole-group absence.
- Repeated owner cancellation during grace or later cleanup cannot interrupt
  the retained cleanup task; the original cancellation propagates afterwards
  with the final evidence and partial capture, and cannot authorize retry.
- Raw coroutine closure does not run awaited OS cleanup; closure is handled
  without attempting asynchronous finalization, and normal Task cancellation
  followed by awaiting remains the supported cleanup lifecycle.
- Grace changes neither tagged termination reasons nor raw integer exit-status
  semantics, including negative signal returncodes; unavailable output remains
  `None`, and zero output limit continues to mean unbounded active capture.

Acceptance requires these focused scenarios:

- Disposable processes exercise zero grace, cooperative SIGTERM and ignored
  SIGTERM.
- An owned pipe-holder survives leader exit and still receives final group
  SIGKILL.
- Cancellation during grace, including repeated cancellation, retains the
  original cancellation and captured prefix while cleanup completes.
- Controlled effect-boundary scenarios exercise SIGTERM and SIGKILL failures
  and budget exhaustion.
- Those failure scenarios verify separate diagnostics, final KILL attempt,
  pipe closure, remaining-budget wait and conservative dispatch refusal.

The implementation includes the listed focused scenarios, which passed
independent review. This child does not provide full Evaluation-harness
integration.

## Additional context

- This child delivers one service, the supervisor, plus the stop hook and
  representative caller boundary that establish AC-3.
- The Evaluation caller and OS/asyncio are external collaborators.
- The parent Evaluation Work owns the full experiment runner, including the
  full caller, trial scheduling, retry policy, budgets, scoring, and evidence
  persistence.
- This boundary governs both typed wiring and implementation.
- Parent AC-3 owns actual harness stop, cleanup, retry-without-overlap,
  active-status, and not-started accounting verification.
- Proportionate reviewed increments inside this Work cover typed architecture,
  typed wiring, and implementation with focused tests rather than separate
  child Works.
- Typed review establishes lifecycle ownership, result/error distinctions, and
  the narrow caller integration before implementation.
- Private helpers and incidental signatures remain flexible under
  [architecture exploration](../../../../../architecture-exploration.md).

The maintainer explicitly authorized implementation of this Work before its
planning PR merges and waived that prerequisite for this Work.

The Evaluation explicitly trusts upstream Codex for internal lifecycle beyond
the owned group. Children do not generally exit when their parent exits, so the
owned-group stop and direct-child wait remain necessary before another attempt.
Codex may spawn children; this Work does not establish
containment of processes that leave that group or whole-host process absence.
OS process-creation latency may not be interruptible by the async deadline; the
boundary must disclose that limit rather than promise a hard creation bound.
These assumptions qualify only the experiment, preserving stronger production
delivery requirements.

Required native evidence uses a few focused disposable scenarios for success,
nonzero exit, timeout, cancellation, positive-limit overflow, zero-limit
capture, invalid limits, and a controlled owned child, plus cleanup-failure and
stop-dispatch accounting. Relevant resource-acquisition failure checks must
observe the public boundary without adding test-only options. These checks
establish deterministic lifecycle behavior, not live Codex isolation or model
quality; the implementation regressions are reported in the architecture
evidence below. Representative caller tests cover only the child boundary; the
actual Evaluation harness still requires parent-owned integration and review.
See
[tests](../../../../../../test/script/integration/test_process_supervisor.py).
All child criteria are DONE within the supervisor and representative caller
scope; actual harness integration remains pending under parent AC-3. The parent
Evaluation Work remains TODO. The
[preparation record](../preparation.md) retains the CLI known issue,
baseline-accounting policy, and exhausted call allowances unchanged.
