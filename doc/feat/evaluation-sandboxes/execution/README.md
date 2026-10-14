# Native execution and retained artifacts

After [enforcement](../enforcement/README.md) and delivery of
[active-state exclusion](../lifecycle/active-state-exclusion/README.md),
deliver
`make sandbox-exec NAME=... EVALUATION_WORK=repository/relative/path
PROMPT='...' MODEL=...`, with optional EFFORT,
PROMPT_FILE instead of PROMPT, and an explicit UUID resume input. Reject absent
or conflicting prompt inputs and implicit/latest-session resume. Wrap existing
native Codex CLI, using its
[non-interactive JSON interface](https://learn.chatgpt.com/docs/non-interactive-mode)
as a primary reference rather than building another agent controller. Use
reviewed findings from the
[communication Investigation](../executor-communication/README.md) to resolve
exec/resume behavior and recovery before implementing that affected routing; its
trials and recommendations do not deliver this wrapper. The
[reconciled map](../README.md#children-and-gates) assigns this outcome
exclusively here, replacing the unimplemented old executor-runtime contract.

Reuse the shared
[root/ownership resolution](../README.md#shared-root-and-ownership), including
optional SANDBOX_ROOT; reject a child belonging to another canonical Git common
directory before invocation. Capture the generation ID before waiting on the
stable per-name OS-held lock used by creation and removal. Acquire automatically
before launch and hold through execution/descendant stoppage and result
retention, following the shared crash/recovery guards. Revalidate the generation
and destination identity; abort before invocation if either changed.

Before initial launch, bind the Evaluation Work and host-controlled owning
orchestrator identity in the persistent private lifecycle marker under the lock.
Validate the required `EVALUATION_WORK` against its README in the owning source
repository/Work branch, not the sandbox frozen clone. Resume must match this
recorded Work/orchestrator identity and exact session UUID; missing or invalid
initial bindings and resume mismatches refuse launch. Reuse the marker for run
identity, known Codex session UUID, outcome and artifact paths. Invalidate
cleanup disposition before initial/resumed execution attempts, including failed
or rejected attempts, under the shared host-update rules. Retain unknown or
incomplete execution after a crash; lock availability alone cannot authorize
resume or removal. The owning orchestrator preserves artifacts and records
explicit cleanup disposition only after maintainer review under the
[shared active-state lifecycle](../lifecycle/active-state-exclusion/README.md).

## Acceptance

- **AC-1 TODO** An approved selected model/effort and accepted readiness admit
  one native initial invocation or explicitly bound UUID resume. Resume retains
  its workspace/private-state identity and enforced boundary. Invalid inputs,
  unavailable model approval, changed readiness, missing/invalid initial Work
  binding, resume ownership mismatch or unrelated UUID fail before invocation;
  the sandbox is visibly active until execution and relevant descendants have
  stopped and results are retained; no manual unlock is required.

  Validation: criterion-marked Make-boundary tests exercise real routing and
  artifact/state effects with a narrow CLI process double, plus independent
  review of effective configuration and model authorization. Verify agreement
  with creation/list/removal, reject a waiter whose captured generation no
  longer matches after claim acquisition, and reject conflicting ownership.
  Cover initial Work paths absent from the frozen clone but valid in the source
  Work branch, missing/invalid paths and resume identity mismatch. An actual
  initial start and exact UUID resume through the new wrapper are required
  before this criterion completes; declare prompts, model/effort, fixtures,
  maximum one initial plus one resume, 15 minutes each/shared 30 minutes, stop
  handling and obtain applicable maintainer approval first. This plan authorizes
  no runs.
- **AC-2 TODO** Success, failure, interruption and timeout preserve changes in
  the workspace. Final message when available, raw JSON events, exit/status,
  elapsed timing boundaries, session identity, artifact paths and reviewer
  artifacts remain on the private side outside child reads. Incomplete final
  messages/events are identified explicitly. Initial output waits for
  independent acceptance before resume; final acceptance/import stays under
  existing review gates. There is no automatic retry or replacement.

  Validation: criterion-marked lifecycle tests inspect retained artifacts and
  automatic lock release only after descendant stoppage and retention for
  partial events, failed CLI, interruption/timeout and rejected resume. Verify
  crash recovery retains unknown outcomes, records known session UUIDs without
  guessing, and invalidates old disposition on new/resumed/failed/rejected
  attempts. Independent review accepts initial output before actual
  resume and final output before import; follow the
  [artifact-import owner](../artifact-import/README.md). Reporting
  interpretation is separate so this leaf remains one bounded native
  execution/preservation review.
