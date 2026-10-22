# Work definition

Read when defining, changing, or reviewing a Work contract. When executing an
Investigation or Evaluation, also read its applicable section below.

Use the [Work contract template](work-contract-template.md) for structure,
outcome writing, and examples. A Work owns one coherent outcome. Its
acceptance criteria follow these rules:

- State independently assessable guarantees or conditions for that outcome.
- Scenarios that establish the same guarantee may stay together.
- Allow non-runtime conditions for guidance, Investigations, and Evaluations.

Work identity and contract discovery follow these rules:

- A Work is identified by its repository directory and has its contract in
  `README.md`.
- Every `README.md` recursively under `doc/feat/` is an active Work contract,
  regardless of contents, including planning parents and Investigations.
- Keep guidance, templates, and retained history outside `doc/feat/`.
- Supporting artifacts may live with a Work, but use filenames other than
  `README.md`; they do not define another contract.
- Do not require YAML frontmatter, a journal, or separate human-facing and
  agent-facing versions of the same contract.

Run `make work-check` to check every active contract. For focused feedback, pass
one or more repository-local Work README paths or subtrees through `ARGS`. The
`make doc-check` target also checks every active contract; its `ARGS` only
focuses its documentation checks.

Apply the [repair and scope rules](change-rules.md#fix-the-underlying-problem)
when assessing existing machinery and the remaining gap. Use an Investigation
when feasibility needs checking. [Work workflow](workflow.md) owns
scope, sizing, planning gates, lifecycle, and promotion of lasting outcomes;
[Work acceptance](acceptance-tracing.md) owns criterion status and evidence.
[Contributor guidance](../CONTRIBUTING.md#work-branches-review-and-merge) owns
branch and PR exceptions.

## Decomposition and architectural exploration

Start with one Work per coherent outcome. Assess decomposition as yes, no, or
unknown: yes means the outcome is coherent as one leaf; no means it contains
independently deliverable outcomes to split; unknown means evidence is needed
to decide. When it is unknown, use the smallest typed architecture exploration
that can answer the remaining question before settling the Work tree.
Exploration may establish that the outcome should remain one leaf, identify
independently deliverable outcomes to split, or frame a bounded Investigation.
It does not authorize implementation of an expanded feature.

[Architecture exploration](architecture-exploration.md) owns the maturity and
review of exploratory, reviewed, and implemented architecture, including how to
retain superseded exploration.
[Work workflow](workflow.md#decisions-and-new-splits) owns the pause, maintainer
decision, and planning-PR gates when exploration finds a new split or scope
change.

Work composition describes which outcomes belong to a parent; scheduling
dependencies describe which Works must precede others. Neither hierarchy is
required to mirror the module hierarchy. Preserve a split's exploration and
rationale with the relevant Work or architecture records.

## Investigations

An Investigation answers a bounded question and recommends a direction. Its
contract states the question, constraints, and decision needed. When comparing
candidates, record each serious candidate's fit, pros and cons, and what was
checked versus what remains uncertain. Conclude with findings and a
recommendation explaining the choice.

A small comparison can stay in one file; link candidate files when that makes
review easier. A supporting Evaluation supplies empirical evidence; it is not
required merely because the Work is an Investigation.

An Investigation may use prototyping to answer feasibility questions through
exploratory implementation. Its contract states the implementation limits and
observable evidence needed to answer the question. Retain findings and observed
execution results as supporting artifacts, including unsuccessful results, and
distinguish them from assumptions.
Production adoption requires a separate reviewed Work contract that addresses
missing production and integration requirements; a successful prototype alone
does not establish production readiness.

## Evaluations

An Evaluation produces empirical evidence for a bounded question under a
declared protocol. It can stand alone or support an Investigation; a small
comparison may stay inline without a separate Work. Its completion does not
adopt a recommendation as policy.

[Empirical evaluation guidance](evaluation.md) owns protocol, observations, and
interpretation requirements. An Evaluation does not require nesting or agents
merely because of its kind.
