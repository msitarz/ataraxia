# Work definition

Read when defining, changing, or reviewing a Work contract. When executing an
Investigation or Evaluation, also read its applicable section below.

Use the [Work contract template](work-contract-template.md) for structure,
outcome writing, and examples. A Work owns one coherent outcome. Its acceptance
criteria state independently assessable guarantees or conditions that establish
that outcome; scenarios for the same guarantee may stay together. Non-runtime
conditions are valid for guidance, Investigations, and Evaluations.

Each Work is identified by its repository directory, with its contract in
`README.md`. Every `README.md` recursively under `doc/feat/` is an active Work
contract, independent of its contents; this includes planning parents and
Investigations. Keep guidance, templates, and retained history outside that
root. Supporting artifacts may live with their Work, but use filenames other
than `README.md`; they do not define another contract. Do not require YAML
frontmatter, a journal, or separate human-facing and agent-facing versions of
the same contract.

Run `make work-check` to check every active contract, or pass one or more
repository-local Work README paths or subtrees through `ARGS` for focused
feedback. `make doc-check` also checks every active contract; its `ARGS` only
focuses its documentation checks.

Apply the [repair and scope rules](change-rules.md#fix-the-underlying-problem)
when assessing existing machinery and the remaining gap. Use an Investigation
when feasibility needs checking. [Work workflow](workflow.md) owns
scope, sizing, planning gates, lifecycle, and promotion of lasting outcomes;
[Work acceptance](acceptance-tracing.md) owns criterion status and evidence.
[Contributor guidance](../CONTRIBUTING.md#work-branches-review-and-merge) owns
branch and PR exceptions.

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
