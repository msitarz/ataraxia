# Completion evidence

Make Work completion require observed acceptance evidence and keep that
evidence usable after the Work directory is removed.

[Acceptance tracing](../../../../acceptance-tracing.md) permits `DONE` when a
method is merely declared, and `ac-check` accepts uncovered `TODO` criteria.
[Work completion](../../../../workflow.md#lifecycle) removes the owning file,
which the acceptance tools require to exist. Neither a successful declaration
check nor full CI alone demonstrates every Work criterion.

Define the completion procedure in the existing owners: account for every
criterion, distinguish declarations from observed results, and specify when
checks run relative to contract removal. Keep a concise criterion-to-result
mapping in the PR, including non-test results and relevant evidence revisions.
Explain how retained test markers referring to removed contracts are treated.
Make this procedure discoverable from Work completion and orchestrator review.
The future owner guidance must distinguish pending criteria from verified
outcomes: do not mark a criterion `DONE` for a declared method or implemented
tests alone.

## Acceptance

- **AC-1 TODO** A Work with passing CI but an unverified criterion cannot be
  presented as complete; the procedure requires evidence for each criterion
  and reports failed, skipped, pending, or unrun verification accurately.
  Verification: walk through passing tests plus a pending manual criterion,
  and a declaration check containing uncovered TODO criteria; review the
  resulting completion decisions in the delivery PR.
- **AC-2 TODO** A completion PR that removes its Work contract has a specified
  verification sequence and retains enough criterion text, results, and
  references for review and resumption without restoring deleted files.
  Verification: walk through one test criterion and one manual criterion from
  verification through contract removal and review of the resulting PR.
- **AC-3 TODO** General completion rules link to their authoritative evidence
  owner and preserve the full CI and maintainer merge gates.
  Verification: follow the Work completion and orchestrator review routes;
  inspect the affected validation rules and any qualifying WDR proposal.
- **AC-4 TODO** The guidance distinguishes pending criteria from verified
  outcomes and does not treat a declared method or implemented tests alone as
  completion.
  Verification: walk through one criterion with a declared/manual method, its
  failing result, and its passing result; confirm the status remains pending
  until the outcome is verified.

Use the current PR and Git evidence model. Introduce tooling only if a concrete
gap requires it; declaration checking should remain distinct from verification.
