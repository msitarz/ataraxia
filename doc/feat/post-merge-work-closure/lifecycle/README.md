# Retain contracts until authorized closure

## Purpose

Let maintainers request PR corrections against the existing contract without
requiring agents to restore and delete it for each review round.

## Goals

- Define retention, explicit closure authorization, and correction recovery.
- Make parent/dependency updates mechanically unambiguous.
- Define closure publication on the same reviewed open PR branch.

## Non-Goals

- Deliver the command or start closing existing Works.
- Replace maintainer acceptance with automated inference.

## Acceptance criteria

### **AC-1 DONE** One lifecycle retains contracts until authorized closure

Acceptance, workflow, orchestrator, contribution, and PR guidance retain
requested and descendant contracts during implementation and review until
explicitly authorized closure.

- Only an explicit maintainer request in the session authorizes closing selected
  completed Works for a reviewed open PR head and covers the resulting
  mechanical closure changes.
- `DONE`, passing tests, ready-for-review status, and implementation or
  PR-revision requests do not imply closure authorization.
- Substantive implementation corrections after approval invalidate affected
  closure authorization; restore already-closed affected contracts and evidence,
  refresh statuses and independent review, and obtain renewed closure
  instruction.
- Corrections before closure update retained contracts and evidence directly;
  routine verification/removal pairs are retired, with restoration reserved for
  corrections after closure.
- Maintainer acceptance, independent review, full CI on the final closure head,
  and maintainer merge retain their distinct responsibilities.

### **AC-2 DONE** Closure reference updates have a deterministic contract

The template and lifecycle guidance define deterministic reference updates for
authorized closure.

- Children and dependencies use `TODO`, `DONE`, or `ABORT` entries that state
  their purpose.
- A change to a child's purpose updates its parent entry's purpose text.
- Closure marks entries for selected completed Works `DONE` and removes links
  to their deleted contracts while retaining purpose text, without requiring
  delivered-outcome summaries or PR references.
- Other live links to deleted contracts are removed deterministically or point
  to lasting owners, with ambiguity stopping closure for maintainer steering.
- Supporting artifacts remain in the current tree only where live documents or
  Works still need them, with Git history preserving deleted committed artifacts
  without mandatory promotion.
- `ABORT` records lifecycle status and does not authorize closing incomplete
  Works under the completed-only closure authority.
- Guidance distinguishes local verified criteria, maintainer acceptance,
  closure authorization, mechanical closure, and merged delivery.

### **AC-3 TODO** Closure publication authority is explicit

Guidance defines the narrowly scoped authority consumed by the future command
and its Make interface, with these boundaries:

- Authorized mechanical closure commits use the same reviewed open PR branch,
  ordinary push semantics, and existing signing/hooks; direct-master publication
  and separate closure PRs are excluded.
- Clean state, exact reviewed and remote tips, completed selected Works, and
  unambiguous reference updates are required; unexpected changes stop
  publication with recoverable state and no force push or protection bypass.
- Full CI must pass on the final closure head before maintainer merge.
- Git branch/worktree cleanup remains a separate post-merge phase or
  reinvocation requiring verified merged closure provenance.
- A WDR records explicit closure authority and deterministic mechanics, amending
  earlier delivery/cleanup decisions without erasing their history.

## Dependencies

- [Work contract template](../../../work-contract-template.md) and
  [Work acceptance](../../../acceptance-tracing.md): supply the delivered README
  contract and evidence model for lifecycle owner edits.

## Links

- [Parent Work](../README.md): delivery boundary and command outcome.
- [WDR workflow](../../../wdr-workflow.md): decision and history ownership.
