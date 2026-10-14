# Sandbox disposability proof Investigation

Determine what evidence lets `sandbox-remove` discard executor commits and
private output while preserving work that has not been accepted or retained.
Compare evidence source, accountable owner, host/child trust boundary, and
preservation semantics for both kinds of material. Removal implementation
depends on this Investigation being completed and merged; its README must then
link to the selected, maintainer-reviewed result before implementation starts.

Use the existing
[artifact-import contract](../../artifact-import/README.md) as the proposed
owner for accepted executor commits, the
[execution contract](../../execution/README.md) for private output, and the
parent's [root and ownership rules](../../README.md#shared-root-and-ownership)
as the ownership boundary. These are planning inputs, not evidence that an
implementation exists or proof that outputs have been delivered.

## Question and candidates

Which checkable evidence should let removal determine that executor commits
and private output are disposable, who owns each check, and how must a failed
or missing check preserve the material?

Compare at least these candidates, separately for commits and private output:

- **Existing delivery evidence:** for commits, prove the exact accepted
  executor tip is present in the designated full-history Work branch, using
  artifact-import's accepted tip/base and import evidence. For private output,
  use existing reviewed Work/PR evidence and an identified retained artifact
  destination, if those records bind the output sufficiently. This reuses
  current owners and avoids another sandbox-side record; it may not prove
  private output was durably retained or bind it to the exact sandbox.
- **Explicit owner disposition:** require a host-side, independently reviewed
  disposition that identifies delivered commits and private output before
  cleanup. This can express output retention more directly; assess whether it
  needs a new acceptance record, who writes and verifies it, and how stale or
  child-controlled claims are rejected.
- **Preserve when proof is incomplete:** permit removal only when there is no
  meaningful executor work or output, otherwise retain the child for manual
  handling. This has the smallest trust surface and safest failure behavior;
  assess whether indefinite retention is acceptable and whether it fulfills
  the cleanup outcome.

Do not assume a clean Git status proves delivery, and do not choose an
unapproved alternate acceptance record. The recommendation must identify
tradeoffs and any maintainer decision required. Do not implement removal, alter
the artifact-import or execution owners, or authorize trial execution.

## Acceptance

- **AC-1 TODO** A bounded comparison explains, for each serious candidate,
  evidence source, responsible owner, host/child trust boundary, commit and
  private-output coverage, failure behavior, and preservation semantics. It
  distinguishes what existing contracts establish from what remains
  unverified.

  Validation: review candidate coverage against the linked creation,
  execution, artifact-import, Work-delivery and PR-evidence contracts; check
  that no child-controlled claim is treated as host proof and no evidence owner
  is silently duplicated.
- **AC-2 TODO** The Investigation concludes with a recommendation and a
  concrete maintainer decision request where choices remain, without itself
  adopting a policy or choosing an unapproved record. Removal's contract can
  be updated to name the accepted evidence and refuse deletion when proof is
  absent or inconsistent.

  Validation: independent review confirms the recommendation follows the
  stated tradeoffs, preserves commits and private output on uncertainty, and
  leaves implementation blocked until this Investigation is completed and
  merged. No code, sandbox probe, or model run is required.
