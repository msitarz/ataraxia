# Retain contracts until post-merge closure

## Purpose

Let maintainers request PR corrections against the existing contract without
requiring agents to restore and delete it for each review round.

## Goals

- Define the transition from reviewed outcomes to merged contracts to closure.
- Make parent/dependency updates mechanically unambiguous.
- Define the limited authority for closure commits pushed directly to master.

## Non-Goals

- Deliver the command or start closing existing Works.
- Replace maintainer acceptance with automated inference.

## Acceptance criteria

### **AC-1 DONE** One lifecycle retains contracts through merge

Acceptance, workflow, orchestrator, contribution, and PR guidance keep contracts
in the implementation PR through corrections and maintainer merge. Requested
parents retain their completed child contracts through the final tree review.
Affected evidence and criterion statuses are refreshed directly when corrections
change an outcome. Pre-publication verification/removal pairs and contract
restoration loops are retired without relaxing acceptance or CI gates.

### **AC-2 TODO** Closure reference updates have a deterministic contract

The template and lifecycle guidance define supported parent/dependency entries
and their exact post-closure form. Closure changes a parent's selected child
entry to its delivered outcome and resolves other current links to the removed
contract using a lasting outcome owner or merged PR reference. Ambiguous prose
is identified for maintainer steering rather than guessed. Supporting artifacts
are preserved or promoted according to the reviewed contract; they cannot be
silently deleted with a README. The guidance distinguishes local verified
criteria, maintainer acceptance, merged delivery, and mechanical closure.

### **AC-3 TODO** Closure publication authority is explicit

Guidance authorizes narrowly scoped mechanical closure commits directly to
master after merged revision verification, using normal push semantics and
existing signing/hooks. It defines stopping and recovery when direct publication
is unavailable or master advances; no protection bypass or force push is
allowed. A WDR records moving cleanup after merge and replacing agent-driven
mechanics, with the required amendment links to earlier delivery/cleanup
decisions.

## Dependencies

- [Work contract template](../../../work-contract-template.md) and
  [Work acceptance](../../../acceptance-tracing.md): supply the delivered README
  contract and evidence model for lifecycle owner edits.

## Links

- [Parent Work](../README.md): delivery boundary and command outcome.
- [WDR workflow](../../../wdr-workflow.md): decision and history ownership.
