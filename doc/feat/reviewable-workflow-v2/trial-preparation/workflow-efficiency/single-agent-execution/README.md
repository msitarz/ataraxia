# Single-agent execution

## Question

For a bounded Work, does direct execution by one agent improve the path to a
reviewable artifact compared with the current orchestrator-to-executor
topology? This differs from
[guidance application](../guidance-application/README.md) on compliance
interventions and [leaf-agent selection](../leaf-agent-selection/README.md) on
model and effort.

## Scope

Compare fresh direct-agent runs with the current direct orchestrator-to-leaf
Luna-low arrangement, which remains the default. Keep implementing model and
effort comparable; report any model mix separately. Hold task, guidance, tools,
and session freshness constant. Measure executor and orchestrator effort,
checks, repeated work, corrections, human steering, reviewable-artifact time,
preservation, and available token or cost data. Use one independent evaluator.
Recommend a task-sensitive change, the current topology, or an inconclusive
result. This Investigation does not change delegation authorization, review
ownership, maintainer approval, merge control, or CI requirements.

## Works

- **TODO** [Protocol and fixture](protocol-and-fixture/README.md): freeze a
  separate, bounded documentation task, prompts, conditions, rubric, measures,
  and decision thresholds. This is protocol planning, not trial evidence.
- **TODO** [Controlled comparison](controlled-comparison/README.md): only after
  the protocol Work is reviewed and integrated, request explicit authorization
  for the nine fresh sessions, execute three matched pairs, and report results.

The child Works need their own reviewed parent plan integrated before
execution. No trial dispatch is authorized by this Investigation or its earlier
protocol draft. Do not use this Investigation as the fixture: completing it
depends on the same trial and authorization decisions being evaluated.

## Acceptance

- **AC-1 TODO** The protocol compares fresh direct-agent and current topology
  runs using matched Work, prompt, conditions, and comparable implementation
  model/effort, with any model-mix trial kept separate.
  Verification: inspect the declared protocol and both initial handoffs.
- **AC-2 TODO** Results include executor and parent effort, independent
  evaluation, checks, repeated work, corrections, steering, reviewable-artifact
  time, preservation, and available or unknown token/cost data.
  Verification: trace each trial result to the declared measures and gates.
- **AC-3 TODO** The recommendation is evidence-backed, reports limitations,
  and does not imply policy exceptions, agent authorization, or automatic
  adoption.
  Verification: compare the conclusion with declared thresholds, trial
  conditions, and existing owner/maintainer approval requirements.
