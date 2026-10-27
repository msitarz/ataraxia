# Coordinator lifecycle design

**Status:** Exploratory proposal for review; the existing runtime skeleton is
unchanged and all Work acceptance criteria remain TODO. The
[Work contract](README.md) owns behavior and the
[current architecture](architecture.md) describes implemented components.
[PR 405](https://github.com/msitarz/ataraxia/pull/405) is a superseded approach
with known lifecycle bugs, not a validated alternative.

## TL;DR

- One coordinator owns run tasks, shutdown, and finalization for one provider.
- One typed state per call and one typed quota lifecycle own live facts.
- Small pure decisions select transitions while ordinary async functions own
  effects.
- Progress derives from those states and durable records rather than a second
  ledger.
- Existing consumer ports and the flat persisted `CallRecord` schema remain
  unchanged.
- The [type sketch](design/eval/runner/coordinator/) describes proposed shared
  state boundaries, not runtime implementation or final private signatures.

## Coordinator

- The run owner creates bounded workers and prevents dispatch after stop or
  pause.
- It checks the stop latch and quota gate immediately before every dispatch.
- It holds each attempt slot through the supervisor's bounded cleanup.
- It releases the slot before any retry wait or quota probe.
- Recognized scope exhaustion closes the global gate immediately.
- Active attempts drain and their evidence persists before recovery can probe.
- Stop cancels and settles siblings, retains submitted writes, and finalizes
  truthful accounting.
- Unsafe acquisition or cleanup, overflow, and recording failure stop the whole
  run.
- Such a stop leaves undispatched calls not started.
- Unsafe acquisition or cleanup and recording failure mark the run incomplete.
- This remains true when the unsafe outcome belongs to the last scheduled call.
- No scheduler framework, event bus, extra ports, or process-tree tracking is
  introduced.

## Call lifecycle

| State | Allowed next state | Meaning |
| --- | --- | --- |
| Queued | Attempting, stopped | No attempt has started. |
| Attempting | Recording | The supervisor owns the attempt through cleanup. |
| Recording | Retry wait, queued, finished, stopped, evidence pending | Settlement is known and its write decides what may be claimed. |
| Retry wait | Queued, stopped, evidence pending | A call-local wait is closed durably before dispatch. |
| Finished | None | A durable terminal outcome will not be repeated. |
| Evidence pending | None | A required record failed and no durable result is claimed. |
| Stopped | None | Stop prevents a further attempt. |

- Attempt history belongs to its call, and terminal records remain immutable.
- Infrastructure and capacity allowances are separate finite counts defaulting
  to zero.
- Their jitter policies are independent, and quota retry is independent of
  ordinary retries.
- A retry requires confident no-result evidence, safe cleanup, and durable
  settlement.
- A nonzero exit or capacity text alone does not prove no semantic result.
- Capacity backoff is call-local and cannot block other runnable calls.
- A quota-blocked call waits at the shared gate without owning a second pause.
- Zero jitter yields, and every retry rechecks the global quota and stop gates.
- A completed semantic call is never repeated during recovery.
- Cancellation, overflow, unsafe cleanup, uncertain acquisition, and write
  failure forbid retry.

## Quota lifecycle

| State | Allowed next state | Meaning |
| --- | --- | --- |
| Open | Draining, stopped | Dispatch may proceed unless the run has stopped. |
| Draining | Waiting, stopped | New dispatch is paused while active attempts settle durably. |
| Waiting | Probing, open, stopped | One recovery wait owns cadence, bounds, and its durable events. |
| Probing | Waiting, open, stopped | At most one separately supervised probe is in flight. |
| Stopped | None | Recovery cannot reopen dispatch. |

- Quota opt-in defaults off and off means no passive quota reads or probes.
- No background monitor or active-period probe is created.
- The recovery flow awaits one probe at a time after the drain.
- A finite positive interval and reset hints schedule checks without promising
  availability.
- Only a fresh available observation in the current pause and matching scope
  resumes dispatch.
- The quota adapter owns scope, source ordering, completeness, and freshness.
- The core neither parses CLI JSONL nor interprets answers.
- The cumulative wait bound includes persistence and probe time across pauses.
- The coordinator rereads monotonic time after the awaited probe-preparation
  write and immediately before polling.
- An expired bound forbids a paid probe even if preparation was already
  durable.
- Probe caps count actual dispatches, and a pre-dispatch end retains its
  truthful lifecycle evidence.
- The proposed `ProbePrepared` input journals intent before the final gate.
- If the bound, stop, or cancellation wins after preparation, a
  `ProbeNotDispatched` event closes it without a process record or probe charge.
- `ProbeDispatched` represents an actual poll invocation and increments the
  probe count only when the reader is invoked.
- Its journal write is retained and settled alongside the invoked probe before
  any result is reported or recovery resumes.
- The existing runtime `QuotaProbeStarted` describes actual dispatch but is
  currently written before polling; future wiring replaces that input with
  preparation and dispatch events and adds the not-dispatched closure.
- Existing scheduled and settled probe records remain separate from these
  proposed inputs; this sketch changes no runtime schema or Work contract.
- A timeout that translates cancellation into `TimeoutError` preserves
  exact-request probe evidence from its exception chain.
- That evidence includes process, output, and cleanup observations and is
  persisted before ending recovery.
- A quota-bound timeout is distinct from owner cancellation and never
  establishes success.
- Missing exact-request evidence leaves the run incomplete rather than inventing
  a probe result.

## Settlement and cancellation

- The owner retains every submitted evidence operation through repeated
  cancellation.
- Once a wait-start write succeeds, the owner must durably close that wait and
  retain its `WaitRecord`.
- This applies when cancellation arrives during the retained start write for
  quota or capacity waits.
- Cancellation remains primary, and a recording failure is retained as its cause
  and marks evidence incomplete.
- The supervisor may latch stop before raising `AttemptCancelled`; the latch
  does not consume that cancellation.
- Owner or leaf cancellation triggers sibling cancellation, bounded cleanup,
  evidence settlement, and propagation of the original cancellation.
- Internal stop-induced sibling cancellation is accounted for without replacing
  the initiating reason.
- A bounded quota timeout is recovery control flow rather than owner
  cancellation.
- Durable attempt, wait, probe, and final records precede reports that claim
  them.
- Presentation failures degrade reporting without changing outcomes or masking
  cancellation.

## Progress

- Projection reads call and quota states plus durable attempt and probe history.
- Calls, attempts, and probes have disjoint accounting and are never summed into
  one total.
- Queued, active, retry-wait, stopped-not-started, finished, and
  evidence-pending calls remain distinguishable.
- A cancelled attempt may map to a failed persisted `CallRecord` while progress
  retains cancellation separately.
- Zero exit after timeout or unsafe cleanup is not successful completion.
- Quota ages derive from producer timestamps and unknown values stay unknown.

## Signal ownership

- Standalone composition owns a fresh event loop and installs SIGINT and
  SIGTERM callbacks through that loop.
- Each callback cancels the coordinator task so it stops and settles the run.
- Entry-point ownership avoids taking over an embedding application’s callbacks.
- It removes its callbacks and restores the prior Python signal handlers on
  exit.
- The owner must establish that the loop is fresh before registration, so no
  prior loop callback is displaced.
- An embedded caller retains signal ownership and forwards cancellation to the
  coordinator.
- Python's public asyncio API does not expose an existing loop callback for
  inspection and restoration.
- Taking over an arbitrary existing loop therefore needs a separately reviewed
  ownership mechanism before implementation.
- Calling `signal.signal` alone does not replace or restore an existing asyncio
  loop callback.

## Dependencies and order

- Composition supplies `EvidenceStore`, `AttemptCall`, `OutcomeClassifier`,
  `QuotaStatusReader`, `Runtime`, and `ProgressSink`.
- The run owner depends on call, quota, settlement, and progress functions and
  shared typed states.
- Call and quota decisions depend on validated values and pure policy, not
  concrete adapters.
- Settlement owns retained tasks and evidence effects, while the supervisor owns
  process cleanup.
- Progress is a pure projection before the sink presents it.
- A run freezes its plan, dispatches bounded attempts, persists settlement, and
  only then reports or retries.
- Quota exhaustion closes dispatch, drains active work, persists wait and probe
  transitions, and resumes only on verified availability.
- Shutdown latches stop, cancels and settles owned tasks, closes durable waits,
  finalizes, and propagates the primary control flow.
- The proposed modules are a responsibility map; private helper signatures
  remain flexible.
- Static sketches cannot prove cancellation, persistence, signal restoration, or
  delivered behavior.
