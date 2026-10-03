# Guidance format

## Question

Does an itemized format help agents apply repository guidance more consistently
than paragraph prose? This is distinct from the
[guidance-application Investigation](../guidance-application/README.md), which
tests interventions and session conditions, and the
[completed leaf-agent selection comparison](https://github.com/msitarz/ataraxia/blob/d79a39c45961fd3d58519572a45ccbeae707d443/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/leaf-agent-selection/controlled-comparison/results.md),
which compares model and effort choices.

## Comparison

Select bounded sections of current guidance and prepare itemized variants
against their paragraph baselines. Before any run, have reviewers establish
semantic equivalence: every obligation, exception, route, and ordering meaning
must remain. Do not combine the format comparison with concision or policy
rewrites. The #108 readability concern motivates a trial, not proof of benefit.

Declare task set, repetitions, counterbalanced order, and evaluation rubric
before trials. Match source guidance, task scope, models and effort, tools,
prompts, and fresh-session conditions across variants. Use an independent
shared rubric and blind reviewers to the variant where practical.

Measure violations by stage and severity, requirement preservation,
first-artifact acceptance, corrections, elapsed time through review, and
reviewer effort. Record text or token length as a possible confound, and cost
when available; otherwise report it unknown. Predeclare what quality or
consistency improvement matters and what overhead is acceptable. Recommend
adoption, no change, or an inconclusive result; the trial itself does not adopt
a default format.

## Acceptance

- **AC-1 TODO** Trial variants are semantically equivalent before runs and
  differ in format only, with task conditions and evaluation basis declared.
  Validation: compare each variant against its source for obligations,
  exceptions, routes, and ordering, then inspect the declared trial plan.
- **AC-2 TODO** Evidence records compare the declared quality, preservation,
  violation, correction, elapsed-time, review-effort, and overhead measures,
  including length and unavailable cost limitations.

  Validation: trace each observation and limitation to its predeclared measure.
- **AC-3 TODO** The recommendation follows the predeclared thresholds and does
  not treat readability or one task as evidence for a default-format change.
  Validation: compare conclusion, evidence, and limitations against the
  review rubric and trial basis.
