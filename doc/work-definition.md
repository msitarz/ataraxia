# Work definition

Read when defining, changing, or reviewing a Work contract. When executing an
Investigation, Evaluation, or Prototype, also read its applicable section below.

Use the [Work contract template](work-contract-template.md) for structure,
outcome writing, and examples. Each Work is identified by its repository
directory, with its contract in `README.md`; link supporting `spec.md` or
`design.md` only when useful. Do not require YAML frontmatter, a journal, or
separate human-facing and agent-facing versions of the same contract.

Apply the [repair and scope rules](change-rules.md#fix-the-underlying-problem)
when assessing existing machinery and the remaining gap. Use an Investigation
or Prototype when feasibility needs checking. [Work workflow](workflow.md) owns
scope, sizing, planning gates, lifecycle, and promotion of lasting outcomes;
[acceptance tracing](acceptance-tracing.md) owns criterion status and evidence.

## Investigations

An Investigation recommends a direction for a bounded question. Its contract
states the question, constraints, and decision needed. For each serious
candidate, record fit, pros and cons, and what was checked versus what remains
uncertain. Conclude with a short comparison and recommendation explaining the
choice.

A small comparison can stay in one file; link candidate files when that makes
review easier. A supporting Evaluation supplies empirical evidence; a Prototype
answers feasibility through exploratory implementation. Neither is required
merely because the Work is an Investigation.

## Evaluations

An Evaluation produces empirical evidence for a bounded question under a
declared protocol. It can stand alone or support an Investigation; a small
comparison may stay inline without a separate Work. Its completion does not
adopt a recommendation as policy.

[Empirical evaluation guidance](evaluation.md) owns protocol, observations, and
interpretation requirements. An Evaluation does not require nesting or agents
merely because of its kind.

## Prototypes

A Prototype answers a bounded question through exploratory implementation. Its
contract states the question, limits, and observable evidence needed to answer
it. Record the result in the PR, including unsuccessful results, distinguishing
observed evidence from assumptions.

Before promoting a Prototype to production Work, review missing contracts and
integration requirements; Prototype completion does not imply production
readiness.
[Contributor guidance](../CONTRIBUTING.md#work-branches-review-and-merge) owns
branch and PR exceptions. The common Work lifecycle applies to all kinds.
