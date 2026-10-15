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

`sandbox-exec` invokes only an approved, bound native initial session or exact
UUID resume.

```sh
make sandbox-exec NAME=... EVALUATION_WORK=repository/relative/path PROMPT='...' MODEL=...
```

- Optional inputs are `EFFORT`, `SANDBOX_ROOT` and `PROMPT_FILE` instead of
  `PROMPT`, with absent/conflicting prompts and implicit/latest-session resume
  rejected.
- Both start/resume require selected model/effort approval and current effective
  readiness, refusing unavailable approval or changed readiness without extra
  grants.
- Initial
  [Work/owner binding](../lifecycle/active-state-exclusion/execution-recovery/README.md#binding-and-attempts)
  validates a contained Work with a README in the owning source repository/Work
  branch even when absent from the frozen clone.
- Resume matches recorded host-controlled Work/orchestrator and exact UUID,
  retaining workspace/private-state identity and boundary without
  missing/invalid bindings, ownership mismatch or unrelated sessions.
- Automatic shared locking rejects foreign canonical Git common-directory
  ownership and changed captured generation/native destination identity before
  invocation under
  [shared root/ownership](../README.md#shared-root-and-ownership).
- The sandbox stays visibly active without manual unlock for AC-2's protected
  lifetime.

Completion requires an actual initial start and exact UUID resume through this
wrapper under applicable maintainer approval and frozen prompts, model/effort,
fixtures and stop handling. The maximum is one initial invocation plus one
resume, 15 minutes each and 30 minutes shared; this contract authorizes no runs.

### **AC-2 TODO** Retain work and private results for review

Every outcome preserves workspace changes and attributable private results for
independent review.

- Final message when available, raw JSON events, exit/status, elapsed timing
  boundaries, session identity, artifact paths and reviewer artifacts stay
  outside child access.
- Success, failure, interruption, timeout and rejected resume retain prior
  attempts and honest partial/missing/incomplete/unknown output, with known
  UUIDs recorded without guessing and no automatic retry/replacement.
- [Shared recovery](../lifecycle/active-state-exclusion/execution-recovery/README.md#ac-2-todo-protect-execution-through-safe-recovery)
  holds exclusion through descendant stoppage/retention and blocks unsafe action
  after crashes regardless of lock availability.
- The shared attempt API invalidates disposition before identified
  initial/resumed/failed/rejected attempts, while unsafe identity preserves the
  record.
- Independent acceptance precedes resume and final
  [import](../artifact-import/README.md), and only the owning orchestrator
  records
  [cleanup disposition](../lifecycle/active-state-exclusion/cleanup-disposition/README.md)
  after preservation and maintainer review.

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
