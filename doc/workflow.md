# Work workflow

Read when planning, executing, or delivering a Work. For contract authoring and
review, follow [Work definition](work-definition.md). Read its applicable
[Investigation](work-definition.md#investigations) or
[Evaluation](work-definition.md#evaluations) section when executing that kind of
Work.

## Scope and sizing

Each leaf Work delivers one independently verifiable, coherent capability or
outcome. The five-minute heuristic asks how quickly a maintainer can understand
the outcome, acceptance conditions, inherited constraints, scope, and
relationship to architecture. Substantive implementation review remains
proportional to the change and has no five-minute cap.

Use these scope rules:

- Do not use responsibility count or lines of code alone to predict cohesion or
  review effort.
- Optional prompts may ask what decision or new behavior is under review and
  which concepts the reviewer must understand; they are not required fields or
  headings.
- Give independently assessable guarantees separate criteria.
- Keep multiple scenarios for one guarantee together. These criteria rules do
  not set a criterion quota or require a child Work per criterion.
- Nest independently deliverable outcomes under a parent Work that maps them.
- Do not hide a broad or incoherent scope in a short contract or omit
  consequential details to satisfy the heuristic.
- Keep ordinary manual review and merge gates in force.
- Before dispatch, the owning orchestrator checks whether the outcome and
  contract are quickly understandable.
- Before publication, the owning orchestrator reassesses scope and cohesion in
  the actual diff.

If simplification and suitable reuse cannot keep the outcome coherent, follow
these planning steps:

- The definer iterates concrete child contracts and dependencies under
  independent owner review, following [Definer guidance](definer.md).
- Merge the concrete planning PR before expanded implementation begins.

Routine choices within the agreed contract need no additional approval,
whether its acceptance criteria are in a Work contract or supplied in the
handoff.

## Decisions and new splits

A new split or any needed maintainer decision pauses the entire requested Work
tree, including other active subtrees.

- The discovering owner escalates through its parent owners to the requested
  Work owner.

The requested Work owner coordinates safe stopping points:

- Stop new dispatch and implementation.
- Preserve in-flight artifacts and evidence.
- Report the concrete decision and affected scope to the maintainer.

Contract preparation needed for steering may continue under owner review.

Before a split or required maintainer decision triggers the whole-tree pause,
bounded typed architecture exploration may resolve unknown decomposition
within the currently authorized scope, as described in
[Work definition](work-definition.md#decomposition-and-architectural-exploration).
This permission does not override a pause already in force.

- If exploration identifies a split or scope change, stop dispatch and
  implementation and use the whole-tree pause above.
- Resume only under this section and the
  [plan-before-implementation lifecycle rule](#lifecycle).
- The concrete planning PR must merge before expanded implementation begins.
- Resume only the authorized scope after the maintainer decision and applicable
  planning gates.

Expanded implementation waits for the concrete planning PR to merge; a decision
alone does not bypass that gate. Independent review and merge gates still
apply.

## Lifecycle

A parent README maps its immediate child Works and prerequisite Works in its
Children and Dependencies sections. Apply these rules to Work entries; ordinary
guidance links in Dependencies have no Work status.

- Use `TODO` for an active Work.
- Use `DONE` for a Work whose required outcomes are independently verified.
- Use `ABORT` for a Work stopped with unsatisfied outcomes, including the
  reason.
- Keep completed child Work contracts and architecture artifacts available
  through their parent Work's completion.
- Parent completion does not trigger deletion.
- The maintainer may remove retained records manually after parent completion.
- Update a parent's purpose text when a child's purpose changes.
- Do not require outcome summaries or PR references in parent entries.

Statuses describe the checked-out branch's verified delivery state, not
maintainer acceptance or merge.

- Use `master` to determine integrated status.

The Work criterion status and evidence rules are owned by
[Work acceptance](acceptance-tracing.md#criterion-status). The child does not
duplicate its parent-owned status.

- Merge the concrete requested-tree plan before implementation.
- The owning orchestrator coordinates local delivery maps within that tree under
  [orchestrator ownership](orchestrator.md#roles-and-delegation).
- Executors apply reviewed map updates from their handoff.

Executors need not read orchestrator scheduling guidance for that operation.

- Retain requested and descendant contracts through implementation PR review,
  corrections, and after completion.
- Keep parent entries linked to their contracts.
- Follow [Work acceptance](acceptance-tracing.md#work-delivery) for evidence and
  correction recovery.
- Keep lasting contracts and decisions at their authoritative owners.

PRs hold review discussion; Git preserves merged contracts and exact changes.

- If a Work stops with unsatisfied outcomes, preserve its contract.
- If a Work stops with unsatisfied outcomes, report the remaining outcomes.

There is no required Work closure or post-merge branch and worktree cleanup
procedure.

- Before completing a Work, review tests added during it.
- When completing a Work, read [test ownership](test-ownership.md).

Discovery may add children without maintaining a fixed execution list, following
the [scope and sizing](#scope-and-sizing) and
[decision and split rules](#decisions-and-new-splits). Nest when it reduces
necessary context.

Directory ancestry does not select a Git base.

When acting as orchestrator for repository changes, follow the
[Orchestrator handoffs](orchestrator.md).

When a Work proposes or reviews a consequential delivery-workflow choice,
follow the [WDR workflow](wdr-workflow.md). Routine Work tasks do not need to
read it.
