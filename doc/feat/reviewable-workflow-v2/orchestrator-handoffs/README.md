# Orchestrator handoffs

Define how an orchestrator delegates implementation work to Luna and reviews
the result. This Work establishes future interaction policy; it does not
change the process used to plan or deliver the current Work.

Completion means:

- Require the orchestrator to hand implementation work to Luna at low
  reasoning effort.
  Larger reasoning effort requires maintainer approval. If the requested work
  exceeds a quick, single-responsibility review, split it into nested Works.
- Keep each handoff focused on one responsibility and its acceptance criteria.
  The orchestrator reviews Luna's result, shares concrete findings with the
  same Luna subagent, and continues the review-and-correction loop until the
  findings are resolved. Reuse the same subagent context where available; token
  caching is a possible benefit, not a guarantee.
- Require the orchestrator to report when Luna is unavailable rather than
  silently switching to another implementation path.
- Preserve the maintainer's manual review and merge gate after agent review.
- On completion, update the parent README to `DONE` with the delivered outcome
  and remove this child directory in the same PR, following the
  [Work lifecycle](../../../workflow.md).

This Work defines delegation policy only; it does not implement any WDR or
retirement work.
