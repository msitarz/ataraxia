# Work contracts

Read this file when creating, changing, or reviewing a Work.

Each Work lives in a directory identified by its repository path. Its short
`README.md` states the intended outcome and observable acceptance criteria so
the reviewer can tell when it is complete. Add `spec.md` or `design.md` only
when useful, and link to it from the README.

When defining a Work, apply the
[repair and scope rules](change-rules.md#fix-the-underlying-problem): inspect
current machinery, identify which requirements it already fulfills, and define
the remaining required gap. Reuse suitable existing commands, APIs, helpers,
and evidence. Introduce new machinery only when the existing path cannot
fulfill the required outcome, and explain that limitation. Assess existing
behavior against the required outcome rather than treating it as the intended
contract.

Explain the problem and verified current behavior when relevant. Define
completion with observable examples, including preconditions, action, and
expected outcomes; cover boundaries, failures, or behavior to preserve when
they matter. State scope, non-goals, dependencies, assumptions, and open risks
as useful, separating required contracts from provisional design. Use an
[Investigation](#investigations) or [Prototype](#prototypes) when
feasibility needs checking. For performance claims, give a representative
workload, baseline, measurement method, and success threshold. Scale detail to
the Work; these are prompts, not mandatory fields or headings.

Use standard relative Markdown links. Follow the proportionate descriptions
below for meaningful changes; small changes may need only prose.

Do not require fixed headings, YAML frontmatter, a journal, or separate
human-facing and agent-facing versions of the same contract.

## Describing changes

For meaningful architecture, package/module relationships, interactions or
lifecycle changes, include proportionate before/after visuals. Inspect the
current source or contract first and identify the verified revision; distinguish
that before state from proposed additions, changes and removals. Update a
proposal's description when the verified implementation differs. Label
historical examples and illustrative designs so they cannot be mistaken for
current or approved behavior.

Choose a GitHub-supported Mermaid type suited to the question: flowcharts for
relationships, sequence diagrams for interactions, class diagrams for type
relationships, or state diagrams for lifecycle transitions. Show only the
affected context. Include compact affected public API descriptions for
functions, classes and data structures, with useful signatures, inputs/outputs,
behavior and compatibility changes. Tiny edits may use clear before/after prose.

Put shared context in the parent overview and local detail in the affected leaf;
link between them instead of copying diagrams or API descriptions. These are
content choices, not mandatory headings or a template. Review before/after
accuracy against the source and contract, and run `make doc-check` on real
Mermaid fences for embedded rendering. Rendering checks syntax, not acceptance
or GitHub/browser parity. Visuals support the criterion's method and evidence
under
[acceptance tracing](acceptance-tracing.md#planned-validation-and-evidence).

### Examples

This historical relationship example describes the commit command delivered
between `2a51814` (no `make commit` target) and `25814906` (target and helper
present), verified in their Makefiles and the latter's
[commit helper](../script/commit_command.py). It illustrates an added call path;
the checker and normal Git hooks remain in place.

```mermaid
flowchart LR
    subgraph Before
        G1[git commit] --> H1[Normal Git hooks]
    end
    subgraph After
        M[make commit: added] --> C[Commit helper: added]
        C --> R[Pinned rumdl body formatting]
        C --> V[Existing message checker]
        C --> G2[git commit]
        G2 --> H2[Normal Git hooks]
    end
```

The same historical change can instead show the interaction relevant to a leaf:
previously the caller supplied the message directly to Git; afterward the added
Make route formats an optional body and validates the message before invoking
Git. Validation failure returns before Git; successful validation reaches the
ordinary hooks. A parent can link to this leaf detail while showing only the
shared relationship overview above.

```mermaid
sequenceDiagram
    participant C as Caller
    participant H as Commit helper
    participant G as Git
    C->>H: Subject and optional body
    H->>H: Format optional body and validate message
    alt Formatting or validation fails
        H-->>C: Refusal without calling Git
    else Valid message
        H->>G: Commit existing index
        G->>G: Normal hooks
        G-->>H: Git commit status
        H-->>C: Git commit status
    end
```

For that command's public interface, before: no Make commit target. After:
`make commit SUBJECT='fix: describe change' [BODY='Why it matters.']` commits
the existing index after formatting an optional body and checking the message;
SUBJECT must be nonempty and one line. See
[contribution guidance](../CONTRIBUTING.md#commits-and-pull-requests) for its
use.

An illustrative Python API change, unrelated to repository plans, might say:
before `Catalog.find(key: str) -> Item` raises `KeyError` for missing keys;
proposed `Catalog.find(key: str) -> Item | None` returns `None` instead.
Describe the affected `Catalog` class and returned `Item` data structure, and
require callers to handle the optional result. This small signature/behavior
change needs compact prose; add a class diagram only if type relationships also
change.

A tiny edit can say: “Before, the help text misspells `subject`; after, it
spells `subject` correctly. Arguments and behavior are unchanged.” No diagram is
needed.

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
local delivery maps within that tree follow
[orchestrator ownership](orchestrator.md#roles-and-delegation).

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

## Investigations

An Investigation produces a recommendation for a bounded question. Its README
states the question, constraints, and decision needed. For each serious
candidate, record its fit for the problem, pros and cons, and what was checked
versus what remains uncertain. Conclude with a short comparison and
recommendation that explains the choice.

Use one file for a small comparison; use linked candidate files when they make
review easier. A supporting Evaluation can supply empirical evidence; a
Prototype can answer a question that documentation alone cannot resolve. An
Investigation recommends a direction; a Prototype demonstrates feasibility
through exploratory implementation.

Follow the common Work lifecycle and review rules. On completion, promote the
chosen policy or lasting decision to its authoritative owner. Git and the PR
preserve the comparison artifacts when the finished Work directory is removed.
Do not introduce a separate lifecycle or mandatory template.

## Evaluations

An Evaluation owns empirical evidence for a bounded question from a declared
protocol. It may stand alone or support an Investigation's recommendation;
a small comparison may stay inline without a separate Work. A Prototype
answers feasibility through exploratory implementation. None requires nesting
or agents simply because of its kind.

Follow [empirical evaluation guidance](evaluation.md) for protocol,
observations, and interpretation, and the common Work scope, lifecycle, review,
and evidence rules. Evaluation completion does not adopt a recommendation as
policy.

## Prototypes

A Prototype answers a bounded question through exploratory implementation.
Its Work contract states the question, limits, and observable
evidence needed to answer it. Record the result in the PR, including when the
Prototype is unsuccessful, and distinguish observed evidence from assumptions.

Promote a Prototype to production Work only after reviewing missing contracts
and integration requirements. Prototype completion does not imply production
readiness.

See
[CONTRIBUTING.md's Work review rules](../CONTRIBUTING.md#work-branches-review-and-merge)
for branch and PR exceptions. Do not introduce a separate tracking system,
journal, or mandatory template.

When acting as orchestrator for repository changes, follow the
[Orchestrator handoffs](orchestrator.md).

When a Work proposes or reviews a consequential delivery-workflow choice,
follow the [WDR workflow](wdr-workflow.md). Routine Work tasks do not need to
read it.
