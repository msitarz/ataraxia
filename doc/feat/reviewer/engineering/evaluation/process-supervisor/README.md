# Experimental CLI process supervisor

## Purpose

Provide bounded CLI invocation for the engineering-review experiment without
requiring a production reviewer runner.

## Goals

- Run the system `codex exec` command through a small native async
  boundary with truthful output, exit, and completion accounting.
- Request termination of the owned POSIX process group, await the direct CLI,
  and stop the experiment if that signal/wait step fails.

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

## Mechanisms

- Python `asyncio` owns subprocess creation, stream reading, waiting,
  cancellation, and cleanup for one attempt through an awaitable boundary.
- A dedicated POSIX process group scopes termination to the invocation's owned
  group; a small direct-kill policy is sufficient without a mandatory
  TERM/grace/KILL sequence.
- The Evaluation caller owns dispatch policy, signal handling, and evidence
  accounting, with this child delivering only the call-site integration needed
  for AC-3 alongside the supervisor.

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

At base `40a22224e4006b0e437d63254d5319d47d7aebbf`, the protocol and historical
preparation evidence remain, but there is no active supervisor implementation
or supervisor Make target. The proposed change adds one async invocation
boundary between the Evaluation caller and its system CLI command. The caller
keeps experiment policy; the boundary owns only its subprocess resources and
reports their outcome.

The [reviewed typed design](architecture.md) defines the boundary for a future
implementation. Behavior remains pending; the types and architecture establish
no runtime guarantees.

## Acceptance criteria

### **AC-1 TODO** Async invocation returns bounded, truthful observations

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

### **AC-2 TODO** Termination has bounded, accountable cleanup

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

### **AC-3 TODO** Stop handling prevents further experimental dispatch

The narrow integration with the owning Evaluation caller stops new dispatch
immediately on cancellation or failed or unconfirmed signal/wait cleanup and
preserves truthful incomplete-run accounting.

- `SIGINT` and `SIGTERM` at that owning boundary stop new calls and clean up the
  active invocation through AC-2; `SIGKILL` cannot execute cleanup.
- A cleanup failure marks the run incomplete and forbids another dispatch,
  independently of the protocol's ordinary infrastructure-failure threshold.
- The caller owns the protocol's optional retries; the supervisor runs exactly
  one attempt and never overlaps a retry with an unstopped direct CLI from a
  previous attempt.
- Cancellation, including Ctrl+C and `SIGTERM`, stops evaluation without retry.
- The active call's failure and cleanup status remain inspectable, and planned
  but undispatched calls retain the protocol's not-started accounting.

## Additional context

- This child delivers one service, the supervisor, plus the minimal call-site
  integration that establishes AC-3.
- The Evaluation caller and OS/asyncio are external collaborators.
- The parent Evaluation Work owns the full experiment runner, including the
  full caller, trial scheduling, retry policy, budgets, scoring, and evidence
  persistence.
- This boundary governs both typed wiring and implementation.
- AC-3 retains the caller's stop, cleanup, retry-without-overlap, active-status,
  and not-started accounting obligations.
- Proportionate reviewed increments inside this Work cover typed architecture,
  typed wiring, and implementation with focused tests rather than separate
  child Works.
- Typed review establishes lifecycle ownership, result/error distinctions, and
  the narrow caller integration before implementation.
- Private helpers and incidental signatures remain flexible under
  [architecture exploration](../../../../../architecture-exploration.md).

Implementation waits for the concrete planning PR to merge and subsequent
authorization under [Work workflow](../../../../../workflow.md#lifecycle).

The Evaluation explicitly trusts upstream Codex for internal lifecycle beyond
the owned group. Children do not generally exit when their parent exits, so the
owned-group stop and direct-child wait remain necessary before another attempt.
Codex may spawn children; this Work does not establish
containment of processes that leave that group or whole-host process absence.
OS process-creation latency may not be interruptible by the async deadline; the
boundary must disclose that limit rather than promise a hard creation bound.
These assumptions qualify only the experiment, preserving stronger production
delivery requirements.

Required future evidence uses a few focused disposable scenarios for success,
nonzero exit, timeout, cancellation, positive-limit overflow, zero-limit
capture, invalid limits, and a controlled owned child, plus cleanup-failure and
stop-dispatch accounting. Relevant resource-acquisition failure checks must
observe the public boundary without adding test-only options. These checks
establish deterministic lifecycle behavior, not live Codex isolation or model
quality; none has passed by virtue of this contract. Pending specifications map
scenarios to AC-1, AC-2, and AC-3; see
[tests](../../../../../../test/script/integration/test_process_supervisor.py).
Their strict xfails raise only `NotImplementedError`; they describe intended
observations and establish no runtime behavior. All three acceptance criteria
remain TODO.
The [preparation record](../preparation.md) retains the CLI known issue,
baseline-accounting policy, and exhausted call allowances unchanged.
