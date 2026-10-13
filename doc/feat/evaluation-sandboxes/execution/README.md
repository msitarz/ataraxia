# Native execution and retained artifacts

After [enforcement](../enforcement/README.md) and
[active/removal guards](../lifecycle/README.md), deliver
`make sandbox-exec NAME=... PROMPT='...' MODEL=...`, with optional EFFORT,
PROMPT_FILE instead of PROMPT, and an explicit UUID resume input. Reject absent
or conflicting prompt inputs and implicit/latest-session resume. Wrap existing
native Codex CLI, using its
[non-interactive JSON interface](https://learn.chatgpt.com/docs/non-interactive-mode)
as a primary reference rather than building another agent controller. The
[reconciled map](../README.md#children-and-gates) assigns this outcome
exclusively here, replacing the unimplemented old executor-runtime contract.

Reuse the shared
[root/ownership resolution](../README.md#shared-root-and-ownership), including
optional SANDBOX_ROOT; reject a child belonging to another canonical Git common
directory before invocation.

## Acceptance

- **AC-1 TODO** An approved selected model/effort and accepted readiness admit
  one native initial invocation or explicitly bound UUID resume. Resume retains
  its workspace/private-state identity and enforced boundary. Invalid inputs,
  unavailable model approval, changed readiness or unrelated UUID fail before
  invocation; the sandbox is visibly active until execution has stopped.

  Validation: criterion-marked Make-boundary tests exercise real routing and
  artifact/state effects with a narrow CLI process double, plus independent
  review of effective configuration and model authorization. Verify agreement
  with creation/list/removal and rejected conflicting ownership. An actual
  initial start and exact UUID resume through the new wrapper are required
  before this criterion completes; declare prompts, model/effort, fixtures,
  maximum one initial plus one resume, 15 minutes each/shared 30 minutes, stop
  handling and obtain applicable maintainer approval first. This plan authorizes
  no runs.
- **AC-2 TODO** Success, failure, interruption and timeout preserve changes in
  the workspace. Final message when available, raw JSON events, exit/status,
  elapsed timing boundaries, session identity, artifact paths and reviewer
  artifacts remain on the private side outside child reads.
  Incomplete final messages/events are identified explicitly. Initial output
  waits for independent acceptance before resume; final acceptance/import stays
  under existing review gates. There is no automatic retry or replacement.

  Validation: criterion-marked lifecycle tests inspect retained artifacts and
  released active state for partial events, failed CLI, interruption/timeout and
  rejected resume. Independent review accepts initial output before actual
  resume and final output before import; reuse existing artifact-import
  ownership. Reporting interpretation is separate so this leaf remains one
  bounded native execution/preservation review.
