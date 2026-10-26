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

## Non-Goals

- Interpret reviewer verdicts, validate experiment answer schemas, read private
  labels, score results, or prepare a corpus.
- Own experiment block ordering, repetitions, budgets, retry allowances across
  runs, or scientific claims.
- Add a plugin framework, generic scheduler library, production reviewer, or
  replacement process supervisor.
- Rewrite the existing supervisor's dataclasses.

## Mechanisms

- A Make entry point exposes a small Python `asyncio` context-matrix runner.
- Pydantic validates and serializes or loads the tooling harness's
  configuration, run plan, provenance, and attempt metadata, initially as a
  development dependency with version and model design deferred to
  implementation.
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
- Estimates use a Python token-counting library chosen during implementation
  on the exact composed bytes, and identify the estimation method, library and
  tokenizer versions, and requested-model compatibility; unsupported models
  have unknown or explicitly approximate estimates, never billing precision.
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
- The output directory must be outside the context repository or ignored by
  Git so creating run artifacts does not dirty that checkout.
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
- Retries apply only to explicitly declared process or infrastructure outcomes,
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
  explicitly, with no automatic scanning of prior output or hidden resume.
- A sparse subset that cannot be expressed as one Cartesian product uses
  separate invocations with distinct output directories.
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

The original Work definition authorized no runner implementation, typed
architecture, corpus preparation, or model calls. A later bounded assignment
authorized the architecture proposal and typed boundary. The current
incremental assignment covers shared model records and the input boundary
only; it does not authorize the remaining runner implementation, wiring,
corpus preparation, or model calls.
All acceptance criteria remain TODO, and completion of this generic runner
cannot establish the parent experiment's integrated protections or results.
