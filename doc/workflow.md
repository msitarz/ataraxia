# Work workflow

Read when planning, executing, or delivering a Work. For contract authoring and
review, follow [Work definition](work-definition.md). Read its applicable
[Investigation](work-definition.md#investigations),
[Evaluation](work-definition.md#evaluations), or
[Prototype](work-definition.md#prototypes) section when executing that kind of
Work.

## Scope and sizing

Keep each leaf Work focused on one responsibility and outcome, then size it for
the maintainer judgment needed to review the complete expected change, including
behavior, tests, supporting changes, and concepts to understand. Aim for one
reviewable question or outcome a maintainer can assess in a short sitting of
about five minutes. Responsibility count and lines of code alone do not predict
review effort. Prompts such as what decision or new behavior is under review,
which concepts the reviewer must understand, and whether the result fits one
sitting can help; they are optional guidance, not required fields or headings.

When the expected change needs more review, nest independently reviewable child
Works under a parent that maps their outcomes. Do not push additional scope into
a leaf just because it is nearby. An explicit maintainer request may authorize
a larger review in the current Work PR so the maintainer can steer that
revision; ordinary manual review and merge gates still apply. Approval of a
Work plan alone does not waive the review-effort target if delivery proves
harder to assess, even when scope has not changed.

The owning orchestrator assesses the full expected leaf change against this
target before dispatch and reassesses the actual diff before publication. When
simplification and suitable reuse cannot keep it bounded, the definer iterates
concrete child contracts and dependencies under independent owner review. Merge
the concrete planning PR before expanded implementation begins.

Routine choices within the agreed contract need no additional approval,
whether its acceptance criteria are in a Work contract or supplied in the
handoff.

Strongly recommend at most five Work levels, counting the topmost Work as level
1 and every descendant Work, including leaves. Count Work nodes rather than
helper or specification directories. A proposal beyond five levels requires an
explicit maintainer decision; do not automatically renest existing trees.

## Decisions and new splits

A new split or any needed maintainer decision pauses the entire requested Work
tree, including other active subtrees. The discovering owner escalates through
its parent owners to the requested Work owner, who coordinates safe stopping
points: stop new dispatch and implementation, preserve in-flight artifacts and
evidence, and report the concrete decision and affected scope to the maintainer.
Contract preparation needed for steering may continue under owner review.

Resume only the authorized scope after the maintainer decision and applicable
planning gates. Expanded implementation waits for the concrete planning PR to
merge; a decision alone does not bypass that gate. The explicit scope exception
above still applies, without waiving independent review or merge gates.

## Lifecycle

A parent README maps its immediate child Works. `TODO` links to an active
child's README, `DONE` names the delivered outcome, and `ABORT` records why the
Work stopped. The child does not duplicate its parent-owned status.
Status entries describe the checked-out branch; use `master` to determine
integrated status. Merge the concrete requested-tree plan before implementation;
the owning orchestrator coordinates local delivery maps within that tree under
[orchestrator ownership](orchestrator.md#roles-and-delegation). Executors apply
reviewed map updates from their handoff; they need not read orchestrator
scheduling guidance for that operation.

Delivery or abandonment updates the parent's entry and removes the finished
child directory in the same delivery sequence, following the nested integration
gate in [Work delivery commits](acceptance-tracing.md#work-delivery-commits).
Before removing a finished Work, promote lasting contracts and decisions to
their authoritative owners. PRs hold review discussion; Git preserves removed
contracts and exact changes.

Before removing a completed Work, follow the
[Work delivery commit procedure](acceptance-tracing.md#work-delivery-commits).

After a Work PR merges, follow the
[post-merge branch cleanup](branch-cleanup.md) procedure.

Before completing a Work, review tests added during it. Read
[test ownership](test-ownership.md) when completing a Work.

Discovery may add children without maintaining a fixed execution list, following
the [scope and sizing](#scope-and-sizing) and
[decision and split rules](#decisions-and-new-splits). Nest when it reduces
necessary context. Directory ancestry does not select a Git base.

When acting as orchestrator for repository changes, follow the
[Orchestrator handoffs](orchestrator.md).

When a Work proposes or reviews a consequential delivery-workflow choice,
follow the [WDR workflow](wdr-workflow.md). Routine Work tasks do not need to
read it.
