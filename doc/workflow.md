# Work workflow

Read when planning, executing, or delivering a Work. For contract authoring and
review, follow [Work definition](work-definition.md). Read its applicable
[Investigation](work-definition.md#investigations) or
[Evaluation](work-definition.md#evaluations) section when executing that kind of
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
concrete child contracts and dependencies under independent owner review,
following [Definer guidance](definer.md). Merge the concrete planning PR before
expanded implementation begins.

Routine choices within the agreed contract need no additional approval,
whether its acceptance criteria are in a Work contract or supplied in the
handoff.

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

A parent README maps its immediate child Works and prerequisite Works in its
Children and Dependencies sections. Apply these rules to Work entries; ordinary
guidance links in Dependencies have no Work status.

- Use `TODO` for an active Work, `DONE` for a Work whose required outcomes are
  independently verified, and `ABORT` for a Work stopped with unsatisfied
  outcomes, including the reason.
- Keep a Work's contract link while it is open, including a completed Work
  retained for review; a linked `DONE` therefore differs from an unlinked,
  explicitly closed `DONE`.
- On authorized closure of a selected completed Work, set its Children or
  Dependencies entry to `DONE`, remove its contract link, and preserve its
  title and purpose, whether its prior status was `TODO` or linked `DONE`.
- Update a parent's purpose text when a child's purpose changes; do not require
  outcome summaries or PR references in parent entries.
- Remove other live links to deleted contracts, or retarget them to a lasting
  authoritative owner when the information remains needed; stop for maintainer
  steering when the right disposition is ambiguous.
- Retain supporting artifacts while active Works need them; after authorized
  closure, keep them in the current tree only when live documents or Works need
  them, with Git history preserving deleted committed artifacts and no required
  promotion of every supporting file.
- `ABORT` records lifecycle status and does not authorize closure of an
  incomplete Work by itself. Follow the
  [authorized closure guidance](acceptance-tracing.md#authorized-closure) for
  incomplete outcomes and current tool limits.

For example, either active or completed-but-retained entries become the same
closed entry:

```markdown
- TODO [Child Work](child/README.md): supplies the parser used by the parent.
- DONE [Child Work](child/README.md): supplies the parser used by the parent.

- DONE Child Work: supplies the parser used by the parent.
```

Statuses describe the checked-out branch's verified delivery state, not
maintainer acceptance or merge; use `master` to determine integrated status.
The Work criterion status and evidence rules are owned by
[Work acceptance](acceptance-tracing.md#criterion-status). The child does not
duplicate its parent-owned status.

Merge the concrete requested-tree plan before implementation; the owning
orchestrator coordinates local delivery maps within that tree under
[orchestrator ownership](orchestrator.md#roles-and-delegation). Executors apply
reviewed map updates from their handoff; they need not read orchestrator
scheduling guidance for that operation.

Retain requested and descendant contracts through implementation PR review and
corrections until authorized closure. Keep parent entries linked to their active
contracts through review. Follow
[Work acceptance](acceptance-tracing.md#work-delivery) for evidence, closure
authorization, and correction recovery. Keep lasting contracts and decisions at
their authoritative owners when still needed. PRs hold review discussion; Git
preserves merged contracts and exact changes.

If a Work stops with unsatisfied outcomes, follow
[authorized closure guidance](acceptance-tracing.md#authorized-closure) for
recording `ABORT`; until the checker supports that status, preserve the contract
and pause the incomplete closure request.

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
