# Generic evaluation harness

## Purpose

Run reproducible context combinations through the CLI while retaining raw
observations for caller-owned experiments.

The exploratory [architecture proposal](architecture.md) and its
[typed boundary package](design/eval/) describe one possible
component split; this Work contract remains authoritative.

## Goals

- Compose one selected file from each ordered context directory for every
  requested model and reasoning effort.
- Reuse the existing async process supervisor for bounded concurrent execution
  and inspectable, immutable evidence.
- Let callers run a manual subset again without overwriting earlier evidence.
- Provide a reproducible standalone invocation that can run without a live
  agent conversation.
- Optionally retry eligible transient model-capacity failures with finite
  allowances and bounded backoff with jitter.
- Optionally pause an active run for recognized Codex quota exhaustion while
  preserving frozen inputs, completed outcomes, and caller experiment limits.
- Report execution progress and observed quota state in terminal and redirected
  output without changing retained evidence or experiment ownership.

## Non-Goals

- Interpret reviewer verdicts, validate experiment answer schemas, read private
  labels, score results, or prepare a corpus.
- Own experiment block ordering, repetitions, budgets, retry allowances across
  runs, or scientific claims.
- Add a plugin framework, generic scheduler library, production reviewer, or
  replacement process supervisor.
- Rewrite the existing supervisor's dataclasses.
- Integrate schedulers, install services, maintain launcher liveness, or recover
  a runner after restart.

## Mechanisms

- A Make entry point exposes a small Python `asyncio` context-matrix runner.
- Pydantic validates and serializes or loads the tooling harness's
  configuration, run plan, provenance, and attempt metadata, initially as a
  development dependency with version and model design deferred to
  implementation.
- `tiktoken` supplies the first token-estimation adapter behind the
  consumer-owned, provider-neutral `TokenEstimator` port as a development
  dependency. A first encoding lookup may download and cache vocabulary data
  through tiktoken's native cache; estimates do not call a model API or CLI and
  do not write harness output or evidence.
- [The existing supervisor](../../../../../../script/process_supervisor.py)
  executes each attempt and owns its process acquisition, capture, and cleanup.
- An `asyncio` semaphore limits active attempts until their cleanup settles.

## Inherited constraints

The [parent Evaluation](../README.md#inherited-constraints) owns its integrated
experiment protections and verifies them at its actual invocation boundary; this
child verifies only the generic runner guarantees below with controlled
processes and retained artifacts. The [protocol](../protocol.md) owns reviewer
preparation, validation, scoring, block ordering, budgets, and protected
material, while the [preparation record](../preparation.md) retains its
exhausted allowances and known CLI limitations. The caller must enforce those
requirements when using this runner, including its positive output cap, rather
than infer compliance from generic execution. The supervisor's
[lifecycle limits](../process-supervisor/README.md#additional-context) apply
unchanged, including owned-group scope, uncertain upstream behavior,
non-interruptible process creation, and inability to clean up after `SIGKILL`.
Generic prompts establish neither tool-free execution nor private-data
isolation.

## Acceptance criteria

### **AC-1 TODO** Ordered inputs define a deterministic matrix

A caller can inspect the complete scheduled matrix before any model call.

- The Make entry point accepts repeated ordered `-d`/`--directory`, repeated
  ordered `-m`/`--model`, repeated ordered `-e`/`--effort`, positive integer
  `-c`/`--concurrency`, `-o`/`--output-directory`, `-n`/`--dry-run`, and ordered
  `-s`/`--separator` arguments, plus optional
  `-i FILE`/`--instructions-file FILE`.
- CLI help explains that the instructions-file option passes its frozen staged
  path through Codex's native `-c model_instructions_file=PATH` setting and
  replaces Codex's default system instructions, while `-d` files remain ordinary
  supplied context.
- Dry run uses the same validation, ordered matrix, and frozen source-byte
  composition as execution, held in memory without dispatch; the output
  directory may be omitted because dry run writes no output, while execution
  requires it.
- At least one directory, model, and effort are required, and invalid arguments
  or an empty directory refuse all model calls.
- Before preparation or model calls, the runner resolves one Git repository
  root and HEAD commit SHA once for all supplied context directories and files,
  rejecting external inputs or a missing HEAD.
- The entire repository must have no staged, unstaged, or untracked changes,
  including individual untracked files within directories, before preparation.
- Batched, NUL-delimited Git tracked-file queries scoped to context directories
  confirm every discovered input file is tracked, rejecting ignored or
  untracked inputs without a Git subprocess per file.
- Each directory contributes its immediate regular files in lexical filename
  order without recursion, and selected context files must be regular files
  rather than symbolic links.
- Directory aliases and symbolic links in parent paths resolve normally when
  determining membership in the single context repository.
- Files must decode as strict UTF-8, and invalid encoding or unreadable files
  refuse all model calls before dispatch.
- Each call selects one file from every directory and joins their unchanged
  bytes in directory argument order using the separator for each directory
  boundary, defaulting to exactly two LF bytes.
- A separator argument between successive directory arguments overrides that
  boundary for every selected file combination, preserving directory order
  across intervening flags rather than attaching separators to files.
- Separator arguments before the first or after the last directory argument, or
  multiple separator arguments for one boundary, are rejected before dispatch.
- Separator values allow empty strings and decode only `\n`, `\r`, `\t`, and
  `\\` escapes before UTF-8 encoding, rejecting unknown or dangling escapes.
- The full Cartesian product uses directory argument order with the last
  directory varying fastest, then model argument order, then effort argument
  order for each context combination, retaining repeated arguments as separate
  scheduled positions.
- The runner assigns no instruction or data role to a context directory or file.
- The runner prints the scheduled call count and retains the ordered plan before
  dispatch, without claiming that this order supplies experiment block ordering.
- Dry run prints the scheduled call count and estimated input tokens per
  composed context and model, or a clearly labeled range and aggregate across
  the matrix, accounting for separators and repeated scheduled positions.
- Estimates use the `tiktoken` adapter through `TokenEstimator` on the exact
  composed bytes, and identify the estimation method, library and tokenizer
  versions, and requested-model compatibility; unsupported models have unknown
  or explicitly approximate estimates, never billing precision.
- The `TokenEstimator` consumer contract uses provider-neutral inputs and
  results, allowing alternative adapters without requiring OpenAI-specific or
  `tiktoken` types in consumers.
- Supplied-context estimates exclude unavailable automatic CLI or system
  context, and a configured instructions file receives a separate labeled
  estimate using the same method and compatibility disclosures.
- Dry run applies the same Git validation using read-only Git subprocesses,
  launches no Codex CLI subprocess or model call, including live version probes,
  creates no output directory, and does not mutate retained evidence.
- Dry run may inspect inputs and settings to prepare its report.
- Unsupported model-effort combinations fail explicitly without silently
  substituting either value, and runtime rejection remains a failed attempt.

### **AC-2 TODO** Frozen inputs and execution metadata identify every call

Retained evidence identifies the exact supplied bytes and execution settings.

- Configuration, run-plan, provenance, and attempt-metadata boundaries use
  strict Pydantic validation and reject unknown fields when loading or
  serializing records.
- Validation preserves the declared setting constraints, including zero output
  allowance and finite positive deadlines, without performing Git checks, file
  I/O, or process execution inside validators.
- Before dispatch, the runner freezes all selected source bytes and composed
  prompts in snapshots and records ordered source paths, source SHA-256
  digests, composed-prompt SHA-256 digests, and ordered separator settings and
  exact decoded bytes sufficient to reproduce composition.
- Records retain the resolved repository root, HEAD commit SHA, and ordered
  repository-relative source paths alongside snapshots and digests.
- Batched comparison of selected source snapshots against that commit's blobs
  rejects any byte differences before dispatch or dry-run reporting, so
  concurrent edits cannot falsely attribute snapshot bytes to the commit.
- The pinned HEAD must contain every selected input, without requiring those
  files to have been committed together.
- Dispatch uses those frozen bytes rather than rereading mutable source files.
- Stable call identity includes ordered selected inputs, separator settings and
  bytes, composed bytes, model, effort, and relevant invocation settings, while
  changed effective inputs produce a separate identity.
- Records retain the resolved absolute Codex path, CLI and runner versions,
  requested model and effort, argv, cwd, explicit configuration, and observable
  effective settings, with unavailable runtime bindings or context marked
  unknown.
- A configured instructions file must itself be a regular nonsymlink file and
  passes the same repository containment, clean-checkout, tracked-file, strict
  UTF-8, and frozen snapshot-to-commit-blob checks as context inputs, including
  in dry run.
- Its repository-relative path, exact bytes, and digest are retained separately
  in execution metadata, and execution stages those frozen bytes for the CLI
  rather than rereading the original file.
- Omitting the instructions-file option preserves Codex's default system
  instructions and records no override, with automatic system bytes marked
  unavailable rather than reporting zero system context.

### **AC-3 TODO** Raw evidence survives without replacement or interpretation

Every scheduled call and launched attempt has inspectable evidence.

- Exclusive creation rejects any existing output directory before model calls,
  including when another process creates it concurrently.
- A new output directory may be inside the context repository without being
  ignored by Git; creation and evidence writes follow the clean-repository
  check and input freeze.
- Run artifacts may dirty that checkout and later be reviewed and committed as
  evidence; the next normal run still requires a clean repository under AC-1.
- The runner does not edit Git ignore rules or the index to accommodate output.
- Per-call and per-attempt records are immutable once finalized and preserve
  separate exact raw stdout and stderr bytes apart from metadata.
- Records retain UTC start and end times, monotonic elapsed time, observed exit
  status, termination reason, cleanup observations, and available usage
  telemetry.
- Observed empty output, unavailable output, partial capture, and unavailable
  usage remain distinct, and a positive output cap retains only the supervisor's
  exact captured prefixes with overflow explicit.
- Generic usage extraction preserves raw telemetry and its units without
  parsing reviewer verdicts, validating answer schemas, or scoring answers.
- Recording failure marks the run incomplete and stops dispatch without
  fabricating a successful record or losing the frozen plan's not-started
  status.

### **AC-4 TODO** Bounded dispatch respects cleanup and stop signals

Concurrency never permits a later attempt to bypass required cleanup.

- Execution and cleanup deadlines are positive and finite, retries have an
  explicit finite ordinary infrastructure retry limit defaulting to zero, and
  no hidden retry occurs; optional quota waiting and model-capacity retries
  follow AC-6 and AC-7 separately.
- Ordinary infrastructure retries apply only to explicitly declared process or
  infrastructure outcomes,
  such as launch failure, timeout, or caller-authorized nonzero exit status,
  after safe settlement, without assuming a nonzero exit produced no semantic
  result.
- Completed zero-exit output is never retried based on its content, and
  cancellation, overflow, unsafe cleanup, uncertain acquisition, or recording
  failure never permits retry.
- The experiment caller retains any stricter retry eligibility requirements.
- A semaphore slot remains held through cleanup on success, failure, timeout,
  overflow, or cancellation, and a retry starts only when cleanup permits it.
- The output allowance accepts nonnegative integers, with zero intentionally
  disabling the byte cap and disclosing unbounded capture memory despite finite
  time limits, while positive values preserve the supervisor's overflow
  behavior.
- The public supervisor stop hook is wired before invocation and latches stop
  before fallible recording, with the latch checked before every dispatch.
- `SIGINT`, `SIGTERM`, or task cancellation stop new calls, cancel active work,
  await bounded cleanup, and end the run without retry.
- Unsafe cleanup or uncertain acquisition stops dispatch and marks the run
  incomplete independently of ordinary attempt failures.
- Every planned but undispatched call remains truthfully not started, including
  cancellation and recording failure, and failed attempts never become success.
- Controlled process checks verify the actual runner wiring, concurrency,
  stop-before-recording, output limits, retries, and failure accounting without
  making model calls.

### **AC-5 TODO** Explicit subset reruns preserve experiment ownership

A caller can rerun a manually selected subset as a new run.

- A caller selects directories containing the desired files, models, and efforts
  explicitly, with no automatic scanning of prior output or restart recovery;
  AC-6 permits only explicit continuation within the same live runner process.
- A sparse subset that cannot be expressed as one Cartesian product uses
  separate invocations with distinct output directories.
- A new output directory preserves earlier raw evidence and frozen identities,
  while changed source or configuration remains a separate effective input.
- Usage guidance explains that the caller must reconcile prior attempts against
  experiment retry and budget limits and must not count reruns or cached answers
  as independent trials without its declared protocol.

### **AC-6 TODO** Optional quota waiting preserves the active run

A caller can opt into waiting for recognized Codex quota exhaustion without
restarting the runner or repeating completed calls.

- `--wait-for-quota` defaults off; without it, quota exhaustion receives no
  automatic quota wait or quota retry.
- An optional maximum cumulative quota-wait duration is finite and positive
  when supplied; its precise CLI spelling remains an implementation detail.
- On explicitly recognized Codex quota exhaustion, the coordinator pauses all
  new dispatch globally, lets active attempts settle through bounded cleanup,
  and persists their evidence before waiting or resuming.
- Waiting holds no attempt semaphore slot and leaves no CLI subprocess asleep;
  the live runner uses asynchronous, cancellable waits.
- Waiting preserves the original frozen plan, inputs, invocation settings, and
  completed outcomes; it neither rereads sources nor repeats completed calls.
- A quota-blocked call is eligible for a later attempt only when the recognized
  evidence confidently establishes that it produced no semantic result; a
  nonzero exit alone never establishes eligibility, and reviewer answers are
  not parsed to infer it.
- Quota waits and eligible quota retries are accounted separately from the
  finite ordinary infrastructure retry allowance, including when that allowance
  is zero; every attempt still counts toward any applicable finite caller-owned
  experiment budget or attempt cap.
- With quota waiting enabled, quota probes run only after recognized quota
  exhaustion prevents evaluation attempts from continuing. After active attempts
  settle and their evidence is persisted, the coordinator directly awaits an
  asynchronous quota-recovery polling flow with a configurable finite positive
  interval and at most one probe in flight. Active execution has no background
  quota monitor or periodic probes.
- A consumer-owned asynchronous quota-polling port exposes provider-neutral
  availability observations to the coordinator, which owns the awaited recovery
  flow, cadence, cancellation, and dispatch gates without importing a Codex
  adapter or requiring a separate monitoring task.
- The Codex adapter owns separate supervised `codex exec --json` probes, never
  blocked evaluations repurposed as probes; its fixed probe condition is
  `gpt-6-luna`, effort `none`, minimal nonempty instructions and prompt,
  disabled plugins, tools, and MCP, and a read-only empty working directory.
- The exact unattended CLI recipe and effective restrictions must be validated
  before implementation claims them; the model choice is user-specified, not a
  verified pricing claim, and this contract authorizes no live calls now.
- The adapter binds probe and telemetry sources to the same Codex quota scope
  as evaluation requests; generic orchestration launches no CLI directly.
- Each probe uses the existing supervisor's finite execution and cleanup
  deadlines and output limit, outside evaluation semaphore slots but bounded
  by the single-probe limit, stop latch, and caller operational budget.
- Probe dispatch and failures follow this explicit polling policy rather than
  consuming evaluation infrastructure retry allowances; unknown observations,
  malformed data, scope mismatch, or infrastructure errors stop new dispatch,
  end quota recovery, and mark the run incomplete with inability to continue,
  never availability or an invented reset.
- Probes are explicit potentially billable operations: configuration and usage
  guidance disclose their consumption, and every probe counts separately toward
  the caller's authorized operational budget. Enabling `--wait-for-quota`
  authorizes quota probes; an optional finite nonnegative integer probe budget
  caps them when supplied, with zero permitting no probes and omission adding
  no harness probe-count cap. Caller operational limits still apply.
- With quota waiting enabled, the Codex adapter passively ingests session
  telemetry after each evaluation attempt and probe, correlating the source with
  its `thread.started` ID; concrete file lookup, quota-scope association,
  interpretation, and source validation must be reviewed before use; the core
  receives provider-neutral observations only.
- Telemetry retains producer timestamps and source coordinates; reading a
  snapshot again never refreshes its age, and stale, unknown, or missing data
  cannot fabricate availability.
- During the quota pause only, numeric reset hints cover both exhausted
  five-hour and weekly windows, using the latest relevant exhausted reset as a
  hint; periodic checks can detect earlier availability, while a future hint can
  wake a check before the next interval. Past or repeated hints cannot create an
  immediate polling loop.
- A hint reaching its time never authorizes evaluation dispatch. Only a fresh
  positive availability confirmation for the same quota scope reopens dispatch;
  the source association and freshness rules remain implementation
  prerequisites.
- A probe's Luna availability establishes no other model's capacity; AC-7
  governs model-capacity failures separately. Usage between checks can exhaust
  quota again, so later attempt failures still follow this policy.
- Evaluation retry eligibility still requires confidently no semantic result,
  safe cleanup, preserved frozen inputs, and applicable caller budgets; probes
  never turn failed evaluations into success or replace the selected model.
- After exhaustion, active evaluations settle and their evidence is persisted
  before any new probe or evaluation resumption; no probe launches during this
  settlement. Unsafe cleanup globally stops dispatch, and probe output and
  event persistence also gate resumption.
- A supplied cumulative quota-wait bound or probe-budget limit stops further
  waiting or probing when exhausted and reports blocked and not-started calls
  truthfully; default-off quota waiting causes no extra probes or session reads,
  and dry run performs neither CLI probes nor session-log reads.
- Raw probe stdout and stderr, request settings, start and end timestamps,
  termination and cleanup, classification basis, thread/source association,
  producer observation age, numeric reset hints, scheduled and actual check
  times, wait durations and reasons, and available usage and cost are retained
  separately from evaluation measurements; unknown usage or cost stays unknown.
- Wait, poll, observation, and end events are durably appended as they occur; a
  final summary alone does not account for quota recovery, and recording failure
  stops dispatch and forbids resumption.
- `SIGINT`, `SIGTERM`, task cancellation, or a latched stop cancels an active
  probe, awaits bounded cleanup, persists its evidence, and settles the awaited
  recovery flow without retry; unsafe probe cleanup or uncertain acquisition
  stops the entire run under AC-4.
- Quota recovery returns only after any probe settles and its evidence is
  persisted; no background quota task survives resumption or runner completion.
- Async core ports and filesystem adapters must not block the event loop while
  reading telemetry; waits hold no evaluation slot or sleeping CLI subprocess.
- The runner never switches evaluation models or accounts, purchases capacity,
  or requests quota resets; its explicitly configured probe model does not
  substitute for an evaluation model, and restart recovery remains excluded.
- Controlled checks verify paused-only polling, passive after-attempt ingestion,
  single-probe bounds, reset and periodic wake scheduling during pauses, stale
  and unknown refusal, scope association, budgets, persistence gates, slot
  release, probe cleanup and recovery settlement, and fresh-confirmation-only
  resumption without making model calls.

### **AC-7 TODO** Optional model-capacity retries use bounded backoff

A caller can opt into finite retries for recognized transient model-capacity
failures while preserving the original call and its evidence.

- A capacity-specific nonnegative integer retry allowance defaults to zero and
  is separate from ordinary infrastructure retries and quota waiting; a
  recognized capacity failure cannot bypass this allowance through another
  retry category.
- Capacity classification distinguishes transient model availability from quota
  exhaustion; unknown observations fail explicitly without arbitrary answer
  parsing, and no shared or account-wide capacity limit is inferred.
- Retry eligibility requires evidence confidently establishing that no semantic
  result was produced, followed by safe cleanup and successful evidence
  persistence; a nonzero exit or capacity message alone is insufficient.
- Each retry is a fresh independent invocation of the same model with the same
  frozen prompt, instructions, and invocation configuration, never same-thread
  continuation, model or account switching, or a separate paid availability
  probe.
- Every launched attempt retains raw evidence and counts toward applicable
  caller-owned experiment budgets and attempt caps, including capacity retries.
- The caller supplies finite positive backoff base and cap durations, with cap
  at least base; invalid settings refuse dispatch.
- For zero-based retry index `k`, full jitter samples uniformly from zero
  through `min(cap, base * 2**k)`; the bound is computed with saturation at the
  cap so large indexes cannot overflow.
- The sampled delay is an asynchronous, cancellable wait holding no attempt
  semaphore slot or CLI subprocess; even a sampled zero delay yields control
  before reconsidering dispatch, and the finite allowance prevents a hot loop.
- Backoff affects the blocked call rather than globally pausing unaffected
  calls; any future model-scoped coordination requires an explicit design.
- AC-6's global quota pause gates every capacity retry dispatch, including a
  retry whose backoff has already elapsed.
- Cancellation or a latched stop takes precedence over backoff completion and
  quota resumption; cancellation, overflow, unsafe cleanup, uncertain
  acquisition, or recording failure never permits a capacity retry.
- Exhausting the capacity allowance or caller budget leaves the call truthfully
  failed rather than successful, with remaining planned calls accounted for
  under AC-4.
- Evidence retains classification basis, retry index, base, cap, computed jitter
  bound, sampled wait, actual monotonic wait duration, and wait-end reason and
  attempt outcome, without replacing previous attempts.
- Capacity wait start and end events are persisted as they occur; a failed wait
  event write forbids retry.
- Controlled checks verify classification refusal, no-result eligibility,
  default-zero and finite allowances, caller limits, saturated exponential
  bounds and jitter sampling, zero-delay yielding, slot release, independent
  invocations, quota gating, and cancellation without model calls; the eventual
  design exposes time and randomness dependencies for deterministic checks.

### **AC-8 TODO** Standalone invocation supports external execution

A caller can launch the harness from a terminal or external cron or launchd
job without keeping an agent conversation alive.

- Usage guidance supplies a reproducible command and identifies its working
  directory, dependency setup and versions, authentication and environment
  prerequisites, unattended CLI configuration, output destination, and exit
  meanings for success, failure, cancellation, and incomplete evidence.
- The documented invocation runs without interactive approval requests when its
  declared authentication, permission, availability, and environment
  prerequisites hold; missing prerequisites fail explicitly rather than require
  an agent to answer prompts or silently broaden permissions.
- While alive, the harness owns its child processes, dispatch, retry and wait
  policies, cleanup, and evidence under AC-1 through AC-7, regardless of who
  launched it. One coordinator serves one provider for one run; multi-provider
  CLI configuration and output support remain outside this Work.
- The maintainer or external service owns launch and liveness; scheduler
  integration, service installation, and restart recovery remain outside this
  Work, and no cron or launchd implementation is required.
- The parent Evaluation owns protocol and fixture preparation, authorized
  budgets, the execution handoff, and later analysis against its declared
  metrics and thresholds; harness invocation readiness establishes neither
  Evaluation completion nor authorization to execute.
- Controlled checks exercise the documented standalone entry point's unattended
  behavior and exit meanings without model calls; usage guidance distinguishes
  checked behavior from live CLI and availability prerequisites.

### **AC-9 TODO** Progress reports evidence-backed execution state

A caller can follow a standalone run's progress from a terminal or redirected
text without keeping an agent conversation alive.

- A consumer-owned `ProgressSink` port presents progress separately from the
  durable `EvidenceStore`; persistence remains authoritative, and facts that
  require evidence are published only after their corresponding durable writes
  succeed.
- Reports identify the run and show completed, remaining, and failed scheduled
  calls separately from launched, completed, and failed evaluation attempts and
  quota probes; retries never increase the frozen plan's scheduled call count.
- Call accounting makes clear whether failed calls are included in completed
  totals, and distinguishes queued, running, and retry-wait calls without
  double counting or summing calls, attempts, and probes into one total.
- Reports expose active attempts, retries and their reason, global quota
  pauses, per-call capacity backoff, stopping, and final status, preserving the
  dispatch and stop precedence in AC-4, AC-6, and AC-7.
- The final report distinguishes execution success, failure, cancellation, and
  incomplete evidence, retains not-started calls, and never labels a successful
  process exit as a reviewer verdict `PASS` or scored answer quality; the
  harness does not interpret or score answers.
- Quota reporting consumes existing validated observations and AC-6 quota
  recovery without launching additional model calls or probes, rereading input
  files, or acquiring personal data solely to produce a report.
- Where validated sources supply them, quota reports show per-window usage
  percentages, identified windows and quota scope, reset hints, and observation
  age; unavailable values stay explicitly unknown rather than inferred from
  elapsed time, attempt counts, or an unrelated quota window.
- Observation age uses the producer timestamp and preserves stale or unknown
  status when a snapshot is read again; reset times remain hints and never
  promise availability or reopen dispatch.
- Progress uses stderr, leaving stdout available for normal CLI and dry-run
  results and future structured consumers; compact refresh is permitted on a
  TTY, while redirected output uses useful plain status lines without ANSI
  control sequences, bounded and throttled to avoid per-poll or per-refresh
  floods while retaining meaningful transitions and final status.
- An explicit quiet mode suppresses progress without changing evidence,
  outcomes, dispatch, retries, or quota recovery; precise option spelling,
  rendering layout, and refresh interval remain architecture choices.
- Presentation failures disable or degrade reporting without changing
  evaluation outcomes or retry eligibility, concealing a recording failure,
  or converting incomplete evidence into success; cancellation and interrupts
  still propagate through the runner's stop and cleanup semantics.
- Controlled checks with fake presentation, evidence, quota, and process
  collaborators verify write-before-report ordering, accounting, quota age and
  unknown handling, waits and stopping, output modes, and presentation failure
  isolation without model calls; these checks verify the local reporting
  guarantee and establish no scored experiment result.

## Dependencies

- DONE [Experimental CLI process supervisor](../process-supervisor/README.md):
  Provide bounded CLI invocation for the engineering-review experiment without
  requiring a production reviewer runner.
  It supplies one-attempt execution and the public stop hook reused here.

## Additional context

The original Work definition authorized no runner implementation, typed
architecture, corpus preparation, or model calls. Later bounded assignments
authorized the architecture proposal and typed boundary, shared model records,
the input boundary, and the pure planning wiring. A subsequent bounded
implementation assignment delivered grouping, exact-byte context composition,
and deterministic call-matrix expansion through the public pure planner. The
current bounded assignment implements local `tiktoken` token counting and
its development dependency behind the provider-neutral port. Its approved
first-use vocabulary download and native cache write are documented in the
current architecture. These assignments do not establish CLI integration,
other runner components, corpus preparation, or model calls.
All acceptance criteria remain TODO, and completion of this generic runner
cannot establish the parent experiment's integrated protections or results.

Quota monitoring is a contract amendment only. The maintainer supplied an
[exhausted five-hour quota capture and session telemetry excerpt](quota-capture.md).
The excerpt identifies a candidate numeric reset source, but file correlation,
account and allowance association, freshness, and failure handling still require
review. The authorized future probe condition is recorded there; its unattended
recipe and positive availability evidence also remain prerequisites. An
app-server schema does not establish the exec schema. The architecture, proposed
typed boundaries, and intent-only BDD scenarios describe the earlier polling
amendment; they establish no runtime behavior. No live probes, quota
implementation, or model calls are authorized by this amendment.

The [third-party capacity report](capacity-report.md) supplies motivation for
AC-7, not direct CLI evidence or proof of retry eligibility. Capacity
recognition also remains an unresolved implementation prerequisite. The
architecture records consumer-owned classifier and quota-status ports with
explicit unknown outcomes; their concrete recognition and reset adapters remain
undefined until evidence verifies their sources. No runner implementation or
model calls are authorized by this contract amendment.

Progress reporting remains in this generic harness Work rather than a separate
child Work. Its bounded amendment defines AC-9 before evidence persistence is
implemented; the delivery stage covers this contract, a separately reviewed
typed design, and intent-only BDD scenarios, not runtime implementation. The
contract alone establishes no reporting behavior. It adds no logger, event bus,
adapter framework, monitoring service, scheduler integration, or dependency on
an agent session. All acceptance criteria remain TODO.

The current quota contract limits probes to the awaited recovery flow after
recognized exhaustion and active-attempt settlement. Passive after-attempt
telemetry remains enabled by the quota-wait opt-in. Earlier architecture and
intent-only scenarios describing active-period monitoring require alignment
before they can support implementation review; this amendment establishes no
runtime behavior and authorizes no live probes or model calls.
