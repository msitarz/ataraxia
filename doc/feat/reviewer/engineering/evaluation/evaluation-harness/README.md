# Generic evaluation harness

## Purpose

Run reproducible context combinations through the CLI while retaining raw
observations for caller-owned experiments.

## Goals

- Compose one selected file from each ordered context directory for every
  requested model and reasoning effort.
- Reuse the existing async process supervisor for bounded concurrent execution
  and inspectable, immutable evidence.
- Let callers run a manual subset again without overwriting earlier evidence.

## Non-Goals

- Interpret reviewer verdicts, validate experiment answer schemas, read private
  labels, score results, or prepare a corpus.
- Own experiment block ordering, repetitions, budgets, retry allowances across
  runs, or scientific claims.
- Add a plugin framework, generic scheduler library, production reviewer, or
  replacement process supervisor.

## Mechanisms

- A Make entry point exposes a small Python `asyncio` context-matrix runner.
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
  `-c`/`--concurrency`, and `-o`/`--output-directory` arguments.
- At least one directory, model, and effort are required, and invalid arguments
  or an empty directory refuse all model calls.
- Each directory contributes its immediate regular files in lexical filename
  order, with no recursion and with symbolic-link directories or entries
  rejected rather than followed.
- Files must decode as strict UTF-8, and invalid encoding or unreadable files
  refuse all model calls before dispatch.
- Each call selects one file from every directory and joins their unchanged
  bytes in directory argument order with exactly two LF bytes between files.
- The full Cartesian product uses directory argument order with the last
  directory varying fastest, then model argument order, then effort argument
  order for each context combination, retaining repeated arguments as separate
  scheduled positions.
- The runner assigns no instruction or data role to a context directory or file.
- The runner prints the scheduled call count and retains the ordered plan before
  dispatch, without claiming that this order supplies experiment block ordering.
- Unsupported model-effort combinations fail explicitly without silently
  substituting either value, and runtime rejection remains a failed attempt.

### **AC-2 TODO** Frozen inputs and execution metadata identify every call

Retained evidence identifies the exact supplied bytes and execution settings.

- Before dispatch, the runner freezes all selected source bytes and composed
  prompts in snapshots and records ordered source paths, source SHA-256
  digests, and composed-prompt SHA-256 digests.
- Dispatch uses those frozen bytes rather than rereading mutable source files.
- Stable call identity includes ordered selected inputs, composed bytes, model,
  effort, and relevant invocation settings, while changed effective inputs
  produce a separate identity.
- Records retain the resolved absolute Codex path, CLI and runner versions,
  requested model and effort, argv, cwd, explicit configuration, and observable
  effective settings, with unavailable runtime bindings or context marked
  unknown.
- Replacement system-instruction bytes and digests, when configured, belong to
  execution metadata rather than imposing a semantic role on a context file.

### **AC-3 TODO** Raw evidence survives without replacement or interpretation

Every scheduled call and launched attempt has inspectable evidence.

- Exclusive creation rejects any existing output directory before model calls,
  including when another process creates it concurrently.
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
  explicit finite limit defaulting to zero, and no hidden retry occurs.
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
  explicitly, with no automatic scanning of prior output or hidden resume.
- A new output directory preserves earlier raw evidence and frozen identities,
  while changed source or configuration remains a separate effective input.
- Usage guidance explains that the caller must reconcile prior attempts against
  experiment retry and budget limits and must not count reruns or cached answers
  as independent trials without its declared protocol.

## Dependencies

- DONE [Experimental CLI process supervisor](../process-supervisor/README.md):
  Provide bounded CLI invocation for the engineering-review experiment without
  requiring a production reviewer runner.
  It supplies one-attempt execution and the public stop hook reused here.

## Additional context

This change defines the Work only; it authorizes no runner implementation,
typed architecture, corpus preparation, or model calls.
All acceptance criteria remain TODO, and completion of this generic runner
cannot establish the parent experiment's integrated protections or results.
