# Generic evaluation harness architecture

**Status: exploratory proposal for the generic harness Work.** The Work
contract in [README.md](README.md) owns behavior and acceptance. This proposal
does not authorize implementation or model calls. The sibling
[process supervisor](../process-supervisor/README.md) is implemented and owns
one attempt's process lifecycle; this harness owns plans, dispatch policy, and
run evidence around that boundary.

## TL;DR

- The CLI turns ordered options into one validated, frozen plan before any
  Codex process can start.
- The harness composes exact tracked source bytes and keeps token estimation as
  a replaceable library port until implementation selects a package.
- An async coordinator owns run order, concurrency, stop latching, retries, and
  not-started accounting while calling the existing supervisor once per
  attempt.
- An exclusive evidence store writes immutable run, call, and attempt records;
  persistence failure stops dispatch and leaves the run incomplete.
- Configuration and persisted records use strict, immutable Pydantic models at
  their boundaries; domain decisions and effects stay outside validators.
- Call identity describes effective inputs. Run identity and scheduled
  positions preserve repeated entries and manually selected reruns.
- This boundary stores observations and generic usage telemetry only. The
  caller owns experiment protocol, budgets across runs, ordering claims, and
  interpretation.

## Proposed components

### CLI and ordered settings

**TL;DR:** Parse the public options and preserve their order and positions.

- The CLI owns repeated directory, model, effort, and separator arguments,
  positive concurrency, output destination, and dry-run mode.
- It turns separators into directory-boundary values only after validating
  exactly one separator per boundary; omitted values mean two LF bytes.
- It rejects missing required values and invalid combinations before handing
  control to preparation.
- Dry run follows preparation and planning but does not create output or invoke
  Codex. It may report token estimates when the estimator can identify their
  method and compatibility.
- Effects: argument parsing and diagnostic output only; it does not perform
  Git, source, process, or evidence effects itself.

### Input freezer

**TL;DR:** Resolve and freeze exact tracked source bytes; leave composition to
the pure planner.

- This component resolves one repository root and HEAD for all inputs, checks
  the checkout and tracked-file membership in batches, and rejects paths that
  escape the repository or traverse symbolic links.
- It selects immediate regular files in lexical order, strictly decodes UTF-8,
  and compares each selected snapshot with the corresponding commit blob before
  dispatch.
- It returns the repository root, HEAD, ordered source snapshots, and any
  separately configured replacement instruction bytes with their digest.
- Replacement instructions remain a separate configured input and metadata
  field; no context file receives an instruction or data role.
- Effects: read-only Git subprocesses and filesystem reads. It does not compose
  prompts or make plans. No CLI process or output writes are permitted during
  preparation.

### Plan and boundary records

**TL;DR:** Represent validated settings and frozen work as immutable values.

- A pure composer and planner join the frozen source bytes with the ordered
  boundary bytes, then build the Cartesian product of contexts, models, and
  efforts. Duplicate scheduled positions remain distinct.
- The plan records source paths and digests, prompt digests, commit provenance,
  and exact separator bytes. Execution uses these snapshots and never
  re-reads mutable source files.
- Frozen dataclasses represent in-memory preparation and invocation values.
  Pydantic boundary models cover configuration, ordered option events, source
  snapshots, planned calls, the frozen plan, and persisted records. They use
  `ConfigDict(extra="forbid", strict=True, frozen=True)`; nested settings are
  tuples and immutable scalar or byte values rather than mutable mappings.
- Validators check value constraints only. Git checks, file reads, estimates,
  directory creation, and process execution belong to explicit operations.
- A scheduled position has no effective-call identity until execution resolves
  its CLI binding and invocation settings. The effective identity then includes
  ordered content, exact instruction bytes, model, effort, executable/version,
  and all other settings that can change the invocation. Run identity and
  position distinguish repetitions and duplicate positions. A manual subset
  is a new run; there is no prior-output scan or implicit resume.
- Effects: none. These values describe decisions and observations but do not
  perform them.

### Token estimate port

**TL;DR:** Keep estimation separate from planning and execution.

- A small consumer-owned port accepts exact composed bytes and the requested
  model and returns an estimate with method, library and tokenizer versions,
  and compatibility status.
- The concrete token library is deferred to implementation. A dry-run report
  contains one estimate for every scheduled call; unsupported model
  compatibility is an explicit unknown or approximate estimate, never an
  omitted estimate or billing precision.
- Estimates cover supplied composed context only; unavailable automatic CLI or
  system context is excluded and labeled.
- A configured replacement instruction receives its own separately labeled
  estimate; it is never folded into the supplied-context count without its
  basis being disclosed.
- Effects: local computation only. The port cannot call the model CLI or change
  the frozen prompt.

### CLI binding and request construction

**TL;DR:** Bind runtime settings to frozen call bytes and build the exact
supervisor request.

- Execution resolves the absolute Codex path and observable CLI version and
  settings after the dry-run branch, without probing the CLI during dry run.
- A small request builder consumes a scheduled call's frozen prompt bytes,
  separately frozen replacement instruction bytes, and the resolved binding.
  It returns an effective-call identity and `AttemptRequest`; it does not
  reopen source paths or infer defaults from mutable files.
- When runtime binding is unavailable during dry run, the report marks its
  binding and effective-call identity unknown. It may show a plan identity,
  clearly labeled as such, but never as the effective invocation identity.
- Effects: execution-time CLI path/version probes and request construction.
  Dry run uses neither probe nor request construction.

### Async dispatch coordinator

**TL;DR:** Run independent calls concurrently while gating retries and stopping
globally on unsafe outcomes.

- The coordinator schedules calls in plan order under one concurrency limit.
  Distinct planned calls may execute concurrently; completion order does not
  change their identity or evidence association.
- A retry belongs to its call and starts only after that call's previous
  attempt cleanup permits dispatch. Cancellation, overflow, uncertain
  acquisition, unsafe cleanup, or recording failure latches a global stop and
  prevents any later dispatch.
- The default retry count is zero. Only declared infrastructure outcomes can
  be eligible; a completed zero-exit result is never retried based on output
  content. Nonzero exits require explicit caller opt-in and are still not
  evidence that no semantic result exists.
- The stop hook latches stop before any fallible recording. The coordinator
  checks the latch before each call and attempt. Cancellation stops new work
  and waits for bounded supervisor cleanup.
- It owns process signal handlers and not-started accounting. Concurrency,
  retry count, deadlines, grace, and output allowance have one source: the
  validated run configuration.
- Stop reasons and partial observations remain associated with the original
  control flow. The coordinator does not parse reviewer answers or assign
  semantic meaning to output.
- Effects: async tasks, semaphore, signal registration, and calls to the
  existing supervisor. It does not own subprocess creation or cleanup.

### Evidence store

**TL;DR:** Preserve each run, planned call, and attempt without replacing prior
evidence.

- The store exclusively creates a new output directory, after confirming its
  location is outside the input repository or ignored there.
- It writes finalized metadata and exact stdout and stderr bytes as separate,
  immutable artifacts. Empty output, unavailable output, partial output, and
  unavailable usage remain distinct; observed exit, termination, cleanup,
  timestamps, and available telemetry retain their source and units.
- Each write is atomic at its artifact boundary. If recording fails, the run is
  incomplete, the stop latch is set, and remaining planned calls stay marked
  not started. A recording failure after an attempt does not replace that
  attempt's original exception or cancellation; if no earlier failure is
  active, the recording error is returned as the run failure. The store does
  not fabricate a successful record.
- Every attempt record carries its run ID, call ID, scheduled position, and
  attempt number explicitly. The in-memory observation reuses the supervisor's
  `AttemptResult`, `AttemptCancelled`, or `AttemptFailureEvidence` value rather
  than copying its output, status, and cleanup fields into a second outcome
  type. The strict Pydantic attempt record is only the persisted projection,
  with structured cleanup observations and separate stream artifact references.
  An unexpected original exception remains in control flow with its supervisor
  evidence snapshot when one is available.
- A small optional telemetry extractor may preserve generic usage fields while
  retaining raw stdout. It does not validate answer schemas, parse reviewer
  verdicts, inspect labels, or score results.
- Effects: exclusive directory creation and evidence writes. It never scans
  prior runs or overwrites them.

### Entry point composition

**TL;DR:** Wire adapters once and keep policy in the coordinator.

- The entry point connects CLI settings, input freezing, pure composition and
  planning, the selected token estimator, CLI binding, request construction,
  coordinator, supervisor adapter, and evidence store.
- The existing `script/process_supervisor.py` remains a separate dependency:
  its `AttemptRunner` owns one attempt, while `call_supervisor` forwards the
  outcome and invokes the harness-owned `DispatchStop` hook when cancellation
  or unsafe cleanup requires stopping.
- The composition root owns concrete adapters; domain modules depend on their
  consumer-facing ports. No generic plugin registry or scheduler framework is
  proposed.
- Effects: connects the effects listed above and exposes the CLI entry point.

## Proposed flow

```mermaid
flowchart LR
    CLI[CLI and ordered settings] --> PREP[Read-only input freezer]
    PREP --> PLAN[Pure composer and ordered plan]
    PLAN --> EST[Token estimates]
    EST --> DRY{Dry run?}
    DRY -->|yes| REPORT[Plan and estimate report]
    DRY -->|no| BIND[Resolve CLI binding]
    BIND --> REQUEST[Build effective calls and AttemptRequest]
    REQUEST --> COORD[Async dispatch coordinator]
    COORD --> STORE[Evidence store]
    COORD --> SUP[Existing process supervisor]
    SUP --> OS[CLI process, capture, cleanup]
    STORE --> RUN[Immutable run evidence]
```

The diagram shows proposed harness boundaries. The existing supervisor and its
OS adapter are the only implemented service shown; the remaining boxes are
exploratory. The input freezer performs read-only Git and filesystem effects;
composition and planning are pure. Estimation returns one explicit value for
each planned call, including an unknown value when compatibility is not known.
The dry-run branch never resolves or probes the CLI.

## Type boundary

The adjacent [typed interface](design/evaluation_harness.pyi) sketches only
shared values and the consumer-facing ports needed to review ownership and
effects. It is exploratory, is not importable runtime API, and intentionally
leaves private helpers and concrete persistence formats flexible. It does not
replace or redeclare the supervisor's types.
