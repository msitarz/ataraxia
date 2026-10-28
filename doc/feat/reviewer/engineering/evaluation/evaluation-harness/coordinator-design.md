# Coordinator lifecycle design

**Status:** Reviewed lifecycle design. State records and pure call and quota
transitions, retained-task settlement, and pure progress projection are
implemented. Shared control implements the stop latch and quota gate, including
async waiter notification. The call owner implements attempt dispatch and
settlement, exceptional supervisor evidence, capacity retry waits, and opt-in
passive telemetry through the shared control and settlement boundaries. A
quota-owner skeleton persists a wait start and closes it when the bound or probe
budget forbids polling. Probe recovery, the run owner, and their composition
remain planned, so this is not a complete runner. All Work acceptance criteria
remain TODO. The [Work contract](README.md) owns behavior and the
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
- Existing consumer port responsibilities and the flat persisted `CallRecord`
  schema are retained.
- The evidence lifecycle-input union has the proposed refinement described
  below.
- The [type sketch](design/eval/runner/coordinator/) is a historical reviewed
  reference; runtime state, pure transitions, retained-task settlement, and
  progress projection and call owner are authoritative. Other owner
  declarations remain planned.

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
| Queued | Attempting, stopped | No current attempt is dispatched; earlier attempts may be durable. |
| Attempting | Recording | The supervisor owns the attempt through cleanup. |
| Recording | Observing quota, retry wait, queued, finished, stopped, evidence pending | The attempt write settles before later effects. |
| Observing quota | Recording telemetry, stopped | The opt-in adapter ingests the durable attempt evidence. |
| Recording telemetry | Retry wait, queued, finished, stopped, evidence pending | The observation write settles before it can support recovery. |
| Retry wait | Queued, stopped, evidence pending | A call-local wait is closed durably before dispatch. |
| Finished | None | A durable terminal outcome will not be repeated. |
| Evidence pending | None | A required record failed and no durable result is claimed. |
| Stopped | None | Stop prevents a further attempt. |

- Attempt history belongs to its call, and terminal records remain immutable.
- Infrastructure and capacity allowances are separate finite counts defaulting
  to zero.
- Quota retry is independent of both allowances.
- Infrastructure retry requeues after durable eligibility and yields before
  reconsidering dispatch.
- Only capacity retry uses its configured full-jitter delay.
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
| Waiting | Preparing, open, stopped, evidence pending | One recovery wait owns cadence, bounds, and its durable events. |
| Preparing | Probing, waiting, stopped, evidence pending | A probe intent settles before the final dispatch gate. |
| Probing | Recording, evidence pending | At most one separately supervised probe is in flight. |
| Recording | Waiting, open, stopped, evidence pending | Captured probe evidence must settle before a decision. |
| Evidence pending | None | A required journal or probe write failed. |
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
- The proposed `ProbePrepared` input journals schedule and pause identity before
  the final gate, without inventing an actual poll time.
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
- The coordinator composes call, quota, settlement, and progress owners.
- The call and quota owners depend on shared `control` and state, not on the
  coordinator.
- The package exports `Coordinator` for the planned runner composition boundary.
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

## Shared lifecycle and effect boundaries

- `CallOwner` exposes one call state and its durable history to the run owner.
- `QuotaOwner` exposes one quota state, durable wait and probe history, and
  latest validated observation to the run owner.
- `RunControl` owns the stop latch and dispatch gate shared by those owners.
- With quota waiting enabled, a call owner immediately closes the quota gate on
  recognized exhaustion and retains the first call position and attempt as the
  pause origin.
- The run owner awaits the latched pause notification alongside worker
  completion, without polling or a separate quota-monitor task.
- Workers at the dispatch gate remain blocked while the run owner drains active
  attempts and their writes.
- The call owner uses the existing quota reader after durable attempt settlement
  and writes its validated observation as telemetry.
- A durably recorded matching observation and the first pause origin form the
  typed `PauseTrigger` retained by `RunControl`.
- After draining, the coordinator derives `QuotaWaitContext` from that trigger
  and validated run policy, then awaits `QuotaOwner` recovery.
- An unavailable, unknown, stale, or mismatched trigger cannot open the gate or
  authorize a probe. The owner ends recovery incomplete, stops, and durably
  closes any started wait as unknown; a prepared probe receives a durable
  not-dispatched unknown event. The adapter owns required-window completeness
  and ordering; the pure state checks nonempty known windows, exhaustion, reader
  scope, and inclusive expiry before effects and again after preparation.
- A failed telemetry write retains its `QuotaTelemetryEvent`, error, and
  already durable attempt in the same call's evidence-pending state.
- Passive ingestion and its writes are skipped when quota waiting is disabled.
- Call owners use the coordinator-owned semaphore through supervisor cleanup.
- `settle` retains a submitted task and returns its value or failure alongside
  any concurrent owner cancellation.
- `ProgressView` captures the owners' states and explicit clocks for a pure
  `ProgressSnapshot` projection.
- These ordinary internal classes and functions describe shared ownership, not
  a framework or the final signatures of private helpers.
- Each call state contains its durable attempt history plus at most one current
  attempt or failed attempt-write obligation.
- Before the attempt write settles, `Recording` counts both the call and the
  attempt as active.
- A failed attempt write moves its captured number, evidence, assessment, and
  error to `EvidencePending`.
- `ObservingQuota` and `RecordingTelemetry` count the call as active.
- Their attempt is already durable and counts only in its terminal attempt
  bucket, not as an active or pending attempt.
- A failed attempt write counts one evidence-pending attempt.
- A failed telemetry write counts the call as evidence-pending while its durable
  attempt remains in its terminal attempt bucket.
- A capacity retry wait retains its sampled delay, monotonic start, start phase,
  context, and pending end record. Its prepared phase precedes selection and
  submission of the start write.
- Infrastructure retries project as queued while awaiting a fresh invocation.
- A retained wait-start write that succeeds during cancellation still obliges
  the owner to write its end and retain its `WaitRecord`.
- Each planned position projects into exactly one call bucket: queued, active,
  retry-wait, evidence-pending, stopped-not-started, succeeded, failed, or
  cancelled.
- `Stopped` with no dispatched attempt projects as stopped-not-started; other
  stopped calls project by their recorded failure or cancellation.
- Attempt totals derive from durable call histories plus each active or pending
  attempt, with retries counted only when dispatched.
- Retry allowances are derived from the classified attempt history and current
  invocation, not maintained in a second ledger.
- Probe totals derive from durable probe history plus the one active or pending
  probe; preparation alone never counts as a probe.
- Quota waiting retains its trigger context, pause identity, monotonic start,
  cumulative earlier duration, and start-write phase.
- Probe preparation retains the schedule and pause identity without inventing
  poll timing.
- The exact `QuotaProbeRequest` is constructed at invocation and retained by
  identity through the reader, timeout translation, and evidence settlement.
- Probe recording and failed or missing evidence remain distinct from an active
  poll and retain its request, captured evidence when available, and failure.
- Failed wait or probe journal writes retain each exact obligation and error in
  order rather than claiming durability, including a later closure failure after
  a dispatch journal failure. If a dispatch journal fails, its invoked probe
  state remains attached while the owner settles and records that probe.
- Future evidence-port wiring must accept the proposed preparation, dispatch,
  and not-dispatched inputs in place of the current started input.
- The existing runtime types and evidence port are unchanged by this sketch.

## Pure transition map

The implemented methods live in `script/eval/runner/coordinator/call_states.py`
and `quota_states.py`; shared records live in `state.py`. These state methods
take captured, durable, policy, clock, and control facts as values. They perform
no I/O and own no tasks. The async owners perform and retain each write, read,
sleep, or invocation before passing its result to the next decision. Inputs must
refer to the same call, wait, or exact probe request as the supplied state;
construction and adapter boundaries establish those relationships.

| Method | From and explicit inputs | To and effect boundary |
| --- | --- | --- |
| `Attempting.capture` | `Attempting`, captured supervisor evidence and classification | `Recording`; the owner submits its attempt write. |
| `Recording.persisted` | `Recording`, durable record, configuration, stop and prepared capacity-wait facts | Durable history with `ObservingQuota`, `RetryWait`, `Queued`, `Finished`, or `Stopped`; policy and independent allowances select the next step, and the owner submits any selected wait start. |
| `ObservingQuota.capture` | `ObservingQuota` and captured event | `RecordingTelemetry`; the owner submits its telemetry write. |
| `RecordingTelemetry.persisted` | `RecordingTelemetry`, configuration, stop and prepared capacity-wait facts | Retry wait, queue, terminal outcome, or stop after the telemetry write settles. |
| `Recording.write_failed`, `RecordingTelemetry.write_failed`, `RetryWait.write_failed` | The respective in-flight call state, exact failed wait input when needed, and error | `EvidencePending`, retaining the obligation and already durable history. |
| `RetryWait.started` | `RetryWait`, settled start, cancellation/stop and pending closure facts | Durable-start `RetryWait`; the owner closes it before propagating cancellation or stop. |
| `RetryWait.completed` | `RetryWait`, durable end record and stop | `Queued` or `Stopped` after appending the wait to history. |
| `Draining.started` | Drained `Draining`, submitted wait, settled start, cancellation/stop and pending closure facts | Durable-start `Waiting`; the owner closes it before stop or cancellation propagates. |
| `PreparingProbe.dispatch_gate` | `PreparingProbe`, fresh policy, budget, remaining time, stop, cancellation, reader scope and closure timing | Permission to invoke or `ProbeNotDispatched`; the owner journals closure or builds the actual request at invocation. |
| `PreparingProbe.dispatched` | `PreparingProbe`, request built at invocation | `Probing`; the owner retains the dispatch journal write alongside the probe. |
| `Probing.capture` | `Probing`, captured exact-request outcome or missing evidence and error | `RecordingProbe` or `ProbeEvidencePending`; the owner extracts exception-chain evidence and writes captured evidence. |
| `RecordingProbe.persisted` | `RecordingProbe`, durable record and history, fresh stop, bound and clocks | Updated probe history and `Waiting`; a required end record remains pending for the owner to write. |
| `Waiting.completed` | `Waiting`, history, durable end record, fresh stop, bound and time | Updated history and `Open` or `QuotaStopped`; this is the only quota transition completing the wait, and only a verified available closure opens. |
| `journal_failed`, `RecordingProbe.write_failed` | In-flight quota state, exact failed obligation or captured probe and error | The corresponding pending state retains the error and evidence. |

Stop and bound facts are sampled again after awaited writes. The stop latch can
close dispatch immediately while quota-state completion awaits the durable wait
closure. Cancellation remains primary in `RunControl` and settlement; a
transition does not consume it. The quota adapter establishes scope,
completeness, ordering, and freshness; the core uses its typed observation
without parsing CLI output. These signatures describe shared decisions, leaving
incidental updates and private helpers flexible.

## Run lifecycle

| Phase | Owner responsibility |
| --- | --- |
| Running | Dispatch bounded workers while the stop and quota gates allow it. |
| Stopping | Latch the first stop, preserve later owner or leaf cancellation, and cancel siblings. |
| Settling | Join attempts, probes, retained writes, and durably close started waits. |
| Finalizing | Write truthful final accounting and then report its durable outcome. |
| Finished | Return or propagate the primary control flow after all owned work settles. |

- These phases describe structured control flow and need no class per phase.
- A supervisor stop latched before a leaf cancellation cannot consume that
  original cancellation or prevent sibling cancellation.
- Internal stop-induced sibling cancellation does not replace the initiating
  reason.
- Finalization is a retained write, including when cancellation repeats.
- If finalization fails during cancellation, cancellation remains primary and
  the write failure is retained as its cause.
- A final write failure otherwise marks the run incomplete and prevents a
  successful final report.

The quota adapter records `valid_until_utc` from the producer timestamp plus its
configured freshness allowance. Equality with the expiry is fresh; missing or
expired expiry cannot authorize resumption. Reading the same source again does
not extend expiry. The pure quota transitions recheck this fact after durable
probe and wait writes.
