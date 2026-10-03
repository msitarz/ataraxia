# Single-agent execution

## Question

For a bounded Work, does direct execution by one agent improve the path to a
reviewable artifact compared with the current orchestrator-to-executor
topology? This differs from
[guidance application](../guidance-application/README.md) on compliance
interventions and the completed
[leaf-agent selection comparison](https://github.com/msitarz/ataraxia/blob/d79a39c45961fd3d58519572a45ccbeae707d443/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/leaf-agent-selection/controlled-comparison/results.md)
on model and effort.

## Scope

Compare fresh direct-agent runs with the current direct orchestrator-to-leaf
arrangement defined by [orchestrator guidance](../../../../../orchestrator.md).
Keep implementing model and
effort comparable; report any model mix separately. Hold task, guidance, tools,
and session freshness constant. Measure executor and orchestrator effort,
checks, repeated work, corrections, human steering, reviewable-artifact time,
preservation, and available token or cost data. Use one independent evaluator.
Recommend a task-sensitive change, the current topology, or an inconclusive
result. This Investigation does not change delegation authorization, review
ownership, maintainer approval, merge control, or CI requirements.

## Works

- **DONE** Protocol and fixture: froze a bounded documentation task, matched
  nine-session protocol, rubric, measures, thresholds, and dispatch request in
  evidence commit `7e33df59e29160655e1145e50a03a1353acdf36d`. No trial has run;
  explicit maintainer authorization is still required.
- **TODO** [Controlled comparison](controlled-comparison/README.md): only after
  the protocol Work is reviewed and integrated, request explicit authorization
  for the nine fresh sessions, execute three matched pairs, and report evidence.

The child Works need their own reviewed parent plan integrated before
execution. No trial dispatch is authorized by this Investigation or its earlier
protocol draft. Do not use this Investigation as the fixture: completing it
depends on the same trial and authorization decisions being evaluated.

The preserved nine-run protocol still pins Luna-low. Before dispatch, review
and align its conditions with current policy, or obtain explicit maintainer
authorization for those frozen conditions. The policy change does not rewrite
the protocol or authorize new sessions.

## Acceptance

- **AC-1 TODO** The protocol compares fresh direct-agent and current topology
  runs using matched Work, prompt, conditions, and comparable implementation
  model/effort, with any model-mix trial kept separate.
  Validation: inspect the declared protocol and both initial handoffs.
- **AC-2 TODO** Evidence includes executor and parent effort, independent
  evaluation, checks, repeated work, corrections, steering, reviewable-artifact
  time, preservation, and available or unknown token/cost data.
  Validation: trace each trial observation to the declared measures and gates.
- **AC-3 TODO** The recommendation is evidence-backed, reports limitations,
  and does not imply policy exceptions, agent authorization, or automatic
  adoption.
  Validation: compare the conclusion with declared thresholds, trial
  conditions, and existing owner/maintainer approval requirements.
