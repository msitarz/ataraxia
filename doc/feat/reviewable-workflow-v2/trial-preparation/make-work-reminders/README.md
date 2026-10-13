# Make Work reminders

Add short, well-timed Make reminders for the Work sizing and handoff checks
that are easy to omit when executing and completing a Work. At verified
baseline `d72d43e`, `worktree-create` and `ac-check` did not provide a focused
reminder at both lifecycle gates: expected-scope sizing before dispatch and
actual-diff review before publication.

Keep the authoritative rules in
[Work sizing](../../../../workflow.md#scope-and-sizing),
[orchestrator handoffs](../../../../orchestrator.md#review-and-return), and
[PR descriptions](../../../../pull-requests.md#descriptions). Make output should
link to those owners instead of copying their full procedures.

Add a pre-dispatch reminder to `worktree-create` to assess the complete
expected leaf change against the maintainer review target of about five
minutes. When the expected change needs more review, the owner pauses to split
it or obtains an explicit maintainer decision to use a larger review in the
current PR.

Add a discoverable `work-review` checkpoint for the completed local diff, after
Work cleanup and before publication. It prompts the requested Work owner to
assess whether the complete leaf diff can be reviewed in about five minutes. If
not, the owner pauses and asks the maintainer whether to split the Work or
review a larger change. Once resolved, the owner completes reviewed
publication through the normal publisher flow and returns the PR to the
maintainer without waiting for a nudge unless a concrete blocker or decision
needs steering. The orchestrator guidance owns the full delivery sequence.

Keep the prompts advisory: they do not estimate review time, authorize a larger
PR, perform a split, publish a PR, or replace independent review. Keep
`ac-check` focused on acceptance declarations and evidence; it may point to the
final `work-review` checkpoint, but should not duplicate its prompt. Do not add
these lifecycle reminders to routine test, documentation, or CI targets.

- **AC-1 DONE** Before dispatch, `worktree-create` displays a concise reminder
  to assess the complete expected leaf change against a review target of about
  five minutes and pause for a split or explicit larger-review decision when
  needed.

  Validation: a criterion-marked Make integration test observes the reminder
  at the `worktree-create` boundary; manually verify its timing and links
  against Work sizing guidance.
- **AC-2 DONE** `make help` lists a `work-review` checkpoint that reminds the
  requested Work owner to assess the complete leaf diff against a review target
  of about five minutes, pause for maintainer steering if it needs more review,
  and then complete reviewed publication and maintainer handoff.

  Validation: criterion-marked Make tests inspect help and checkpoint output;
  manually verify its post-cleanup, pre-publication timing and links to the
  authoritative sizing and orchestrator guidance, and that routine test,
  documentation, CI, and acceptance checks retain their distinct
  responsibilities.
