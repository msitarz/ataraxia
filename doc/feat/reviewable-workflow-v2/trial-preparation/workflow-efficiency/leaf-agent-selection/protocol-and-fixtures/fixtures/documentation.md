# Documentation fixture draft

**Status:** provisional. No source revision, exact subsection, or preservation
inventory is frozen. This is a task proposal, not a runnable handoff.

## Executor-facing draft

**Proposed file:** `doc/orchestrator.md`.

**Proposed task:** within one bounded subsection selected at freeze, consolidate
repeated explanations while preserving every distinct instruction and its
meaning. Do not add obligations, change ownership or sequence, remove failure
handling, or edit unrelated files. Return the patch and a short account of the
consolidation and checks. Do not commit, push, or create a PR.

**Prompt to finalize:**

> At the frozen base revision `[commit]`, edit only `[confirmed subsection]
> in `doc/orchestrator.md`. Consolidate the repeated explanations identified
> in the fixture scope. Preserve every distinct rule, actor, condition,
> exception, sequence, approval and review gate, failure/recovery behavior, and
> required link. Do not introduce new requirements or edit other files. Run
> the frozen documentation checks and return the patch with their results. Do
> not commit, push, or create a PR.

The bracketed values and final wording must be resolved before dispatch. Use
the exact prompt for all nine runs of this fixture.

**Expected outcome:** only the named subsection changes; redundant explanation
is reduced; the reviewer confirms all baseline requirements and links remain
intact; the declared checks pass.

**Proposed checks:** `make doc-format ARGS=doc/orchestrator.md`,
`make doc-check ARGS=doc/orchestrator.md`, and `git diff --check`. Freeze these
commands before trial dispatch.

## Owning-parent-only material — exclude from leaf handoffs

- **Base revision:** TBD. Select and verify a revision different from the
  baseline used by the earlier
  [prose trial](../../../guidance-application/prose-trial.md). Do not infer or
  copy that trial's answer patch.
- **Exact subsection and duplicate passages:** TBD after the owning parent
  verifies the selected revision. Keep the scope small enough for one bounded
  task and name the included headings and passages in the final prompt.
- **Preservation inventory:** TBD. Before freeze, enumerate each distinct rule
  and link in scope, including its owner, trigger, condition, ordering,
  exception, approval/review gate, stop/recovery behavior, and references.
  Keep this inventory out of the executor handoff.
- **Reference evidence:** TBD. Once historical evidence is verified, cite its
  immutable commit permalink here; do not copy reference text or patches into
  the executor prompt.
- **Setup compatibility:** confirm the chosen revision uses the same available
  locked documentation tooling and guidance snapshot as the other runs.

Until these fields are resolved and independently checked, this fixture is not
frozen and cannot be used for a trial.
