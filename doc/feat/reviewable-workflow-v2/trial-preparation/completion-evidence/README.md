# Completion evidence

Make verified Work outcomes reviewable in Git after the Work contract is
removed. The former guidance treated a declared method or implemented test as
completion evidence and relied on PR evidence after deleting the owning
contract. The [acceptance-tracing owner](../../../../acceptance-tracing.md)
owns observed statuses and a commit-preserving delivery sequence.

## Acceptance

- **AC-1 DONE** A Work with passing CI but an unchecked manual criterion stays
  incomplete; evidence and status are recorded beside the criterion before
  removal.
  Verification: Manual scenario walkthrough of passing CI plus an unchecked
  manual criterion left it `TODO`; only the verification method was declared.
- **AC-2 DONE** Work delivery keeps the contract and verified outcomes in an
  implementation/verification commit, then removes the contract and updates
  the parent in a separate final commit. The merge preserves both commits and
  the PR description does not duplicate criterion mappings.
  Verification: Manual sequence walkthrough traced a test-marked result and a
  manual criterion through verification, a retained-contract evidence commit,
  and a separate removal/parent-map commit; Git history retains both outcomes.
  This manual-only contract has no `covers` markers, so selected-test checks
  do not apply; `ac-check` accepted AC-1–4 declarations while the file existed.
- **AC-3 DONE** Work lifecycle and orchestrator guidance route completion to
  the authoritative acceptance-tracing procedure while retaining full CI and
  maintainer review and merge gates.
  Verification: Manual route walkthrough followed both owner links and
  confirmed CI and maintainer gates remain; WDR 9 records the rationale and
  links the procedure owner.
- **AC-4 DONE** A failed manual outcome remains `TODO`; a later observed and
  recorded passing outcome permits `DONE`. Declarations or CI alone cannot
  substitute for that result.
  Verification: Manual status walkthrough kept a declared criterion `TODO`
  after a failing result, then changed it to `DONE` only after the observed
  passing result was recorded beside it.

This is a guidance walkthrough, not a live experiment. Existing tests and
markers remain under their owners. `ac-check` validates declarations; it does
not execute the manual outcomes recorded above.
