# Make Work reminders

Add short, well-timed Make reminders for the Work sizing and handoff checks
that are easy to omit when executing and completing a Work. The current
`worktree-create` and `ac-check` flows do not provide a focused reminder at
both lifecycle gates: expected-scope sizing before dispatch and actual-diff
review with the maintainer handoff before publication.

Keep the authoritative rules in
[Work sizing](../../../../workflow.md#scope-and-sizing),
[orchestrator handoffs](../../../../orchestrator.md#review-and-return), and
[PR descriptions](../../../../pull-requests.md#descriptions). Make output should
link to those owners instead of copying their full procedures.

Add a pre-dispatch reminder to `worktree-create` to assess the complete
expected leaf change against the quick maintainer-review target. When the
expected change needs more review, the owner pauses to split it or obtains an
explicit maintainer decision to use a larger review in the current PR.

Add a discoverable `work-review` checkpoint for the completed local diff,
after Work cleanup and before publication. It prompts the orchestrator to
reassess actual review effort and, if the change remains too large, pause for
the required split or explicit larger-review decision. It also prompts the
orchestrator to return the artifact and revision, outcome, acceptance evidence,
commands run, unrun checks, unresolved criteria, and blockers. Keep this
maintainer handoff separate from the PR description, which follows its own
template and must not gain evidence inventories.

Keep the prompts advisory: they do not estimate review time, authorize a larger
PR, perform a split, publish a PR, or replace independent review. Keep
`ac-check` focused on acceptance declarations and evidence; it may point to the
final `work-review` checkpoint, but should not duplicate its full handoff
prompt. Do not add these lifecycle reminders to routine test, documentation, or
CI targets.

- **AC-1 TODO** Before dispatch, `worktree-create` displays a concise reminder
  to assess the complete expected Work change against the maintainer review
  target and pause for a split or explicit larger-review decision when needed.

  Validation: a criterion-marked Make integration test observes the reminder
  at the `worktree-create` boundary; manually verify its timing and links
  against Work sizing guidance.
- **AC-2 TODO** `make help` lists a `work-review` checkpoint that prompts the
  orchestrator to assess the final local diff and prepare the complete
  maintainer handoff before publication, while keeping that handoff separate
  from the PR description and leaving publication to the normal publisher
  flow.

  Validation: criterion-marked Make tests inspect help and checkpoint output;
  manually verify its place after cleanup and before publication, its links to
  the authoritative guidance, and that routine test, documentation, CI, and
  acceptance checks retain their distinct responsibilities.
