# Native execution and retained artifacts

## Purpose

Run an approved native Codex session against a managed sandbox while retaining
its work and private results through failure and recovery.

## Goals

- Expose explicit initial and exact-session resume inputs through sandbox-exec.
- Apply shared readiness, ownership and exclusion before invocation.
- Retain workspace changes and attributed private artifacts for independent
  acceptance.

## Mechanisms

- The native Codex CLI supplies non-interactive exec/resume through its
  [JSON interface](https://learn.chatgpt.com/docs/non-interactive-mode).
- `make sandbox-exec` wraps that interface using shared readiness and lifecycle
  APIs rather than a second agent controller.
- The private lifecycle marker and artifact area retain attributable attempts,
  session identity and output outside child access.

## Acceptance criteria

### **AC-1 TODO** Invoke only the approved bound session

`make sandbox-exec NAME=... EVALUATION_WORK=repository/relative/path PROMPT='...' MODEL=...`
admits one approved native initial invocation or explicit UUID resume, with
optional `EFFORT`, `PROMPT_FILE` instead of `PROMPT`, and `SANDBOX_ROOT`.
Absent/conflicting prompt inputs and implicit/latest-session resume fail before
invocation. Selected model/effort approval and current effective readiness are
required for both start and resume; changed readiness or unavailable approval
refuses launch without extra grants.

The command consumes shared
[root/ownership resolution](../README.md#shared-root-and-ownership) and
[attempt binding](../lifecycle/active-state-exclusion/execution-recovery/README.md#binding-and-attempts).
Initial `EVALUATION_WORK` must identify a contained Work with a README in the
owning source repository/Work branch, even when absent from the frozen clone.
Resume matches recorded host-controlled Work/orchestrator identity and exact
UUID,
retaining workspace/private-state identity and the enforced boundary. Missing or
invalid binding, ownership mismatch or unrelated UUID refuses launch.

Automatic acquisition uses the stable per-name lock shared with
creation/removal. It rejects foreign canonical Git common-directory ownership
and aborts before invocation if the captured generation or native destination
identity changed while waiting. The sandbox is visibly active under shared
exclusion, without manual unlock; AC-2 owns its protected lifetime.

Completion requires an actual initial start and exact UUID resume through this
wrapper. Before execution, the frozen protocol declares prompts, model/effort,
fixtures and stop handling and obtains applicable maintainer approval. Its
maximum is one initial invocation plus one resume, 15 minutes each and 30
minutes shared. This contract authorizes no runs.

### **AC-2 TODO** Retain work and private results for review

Success, failure, interruption and timeout preserve workspace changes. Final
message when available, raw JSON events, exit/status, elapsed timing boundaries,
session identity, artifact paths and reviewer artifacts remain private and
inaccessible to child commands. Partial/missing final messages and events are
explicit; known UUIDs are recorded without guessing, and earlier attempts
survive failure/resume. There is no automatic retry or replacement.

[Shared execution recovery](../lifecycle/active-state-exclusion/execution-recovery/README.md#ac-2-todo-protect-execution-through-safe-recovery)
keeps exclusion through descendant stoppage and result retention. Crashes retain
incomplete/unknown outcomes and block unsafe action; lock availability alone
authorizes neither resume nor removal. The shared attempt API invalidates prior
disposition before identified initial/resumed attempts, including
failed/rejected requests, while unsafe identity preserves the record.

Initial output requires independent acceptance before resume; final output
requires independent acceptance before [import](../artifact-import/README.md).
The owning orchestrator preserves artifacts and records cleanup disposition only
after maintainer review under the
[disposition contract](../lifecycle/active-state-exclusion/cleanup-disposition/README.md).
Reporting interpretation remains with its separate owner.

## Dependencies

- **TODO** [Enforced runtime readiness](../enforcement/README.md): supplies
  accepted effective start/resume gates before invocation.
- **TODO**
  [Per-sandbox active-state exclusion](../lifecycle/active-state-exclusion/README.md):
  supplies identity, automatic exclusion, attempt recovery and disposition
  invalidation.
- **TODO**
  [Executor communication Investigation](../executor-communication/README.md):
  reviewed findings resolve affected native exec/resume routing and recovery
  before implementation; its trials do not deliver this wrapper.

## Links

- [Reconciled ownership map](../README.md#children): assigns this wrapper
  exclusively here, superseding the undelivered old executor-runtime contract.
