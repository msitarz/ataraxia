# Human review effort

Refine the Work sizing and orchestration guidance so each leaf is planned around
the human judgment its review requires. The recent coverage-checker Work stayed
within one responsibility, yet still took substantial effort to understand;
responsibility count and diff size alone do not predict review effort.

Read the [Work workflow](../../../workflow.md), especially
[scope and sizing](../../../workflow.md#scope-and-sizing), and the
[orchestrator handoff rules](../../../orchestrator.md).

## Acceptance

- Update the Work owner to size a leaf by its complete expected change,
  including behavior, concepts, tests, and supporting changes, with one
  reviewable question or outcome and about five minutes of human judgment as the
  aim. Lines of code are not a review-effort limit.
- Give Work authors prompts that help anticipate the reviewer's decision,
  behavior or concepts to understand, and whether the result can be assessed in
  one short sitting. Treat these as planning prompts, not mandatory metadata,
  headings, or fields.
- Add orchestrator checkpoints before handoff to assess expected review effort
  from the Work contract and before marking a PR ready to reassess the actual
  diff. If either assessment exceeds a quick review, propose independently
  reviewable child Works and review the plan before expanding the delivery.
- Preserve the current scope-steering rule: an explicit maintainer request may
  authorize a larger review in the current PR, but it does not waive human
  review or merge. Approval of a Work plan alone does not waive the review-
  effort target when delivery proves harder to assess, even if its scope has not
  changed.
- Keep the guidance concise and in its existing owners; do not add a required
  estimate field or duplicate Work and orchestrator procedures.

This Work defines the policy change; it does not implement that policy before
its contract is reviewed.
