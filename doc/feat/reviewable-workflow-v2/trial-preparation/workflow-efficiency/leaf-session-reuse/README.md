# Leaf-session reuse

## Question

For one bounded leaf Work, should the implementing executor handle all
correction exchanges, or should each correction use a fresh executor? Current
guidance favors the same executor session under
[orchestrator guidance](../../../../../orchestrator.md). Unlike the
[guidance-application Investigation](../guidance-application/README.md) on
orchestrator sessions or
[completed leaf-agent selection comparison](https://github.com/msitarz/ataraxia/blob/d79a39c45961fd3d58519572a45ccbeae707d443/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/leaf-agent-selection/controlled-comparison/results.md)
on model and effort, this tests correction continuity within one leaf Work.

## Comparison

Compare one executor for initial implementation and all corrections with a
fresh executor at each correction exchange. Every leaf Work starts fresh in
both conditions; do not reuse across Works. Match task, guidance, model and
effort, tools, check policy, handoff information, and reviewer conditions.
Use common independent review and consolidated findings.

For a replacement executor, provide the current Work, artifact and branch,
evidence, and the same consolidated findings, but not the conversation
history. Measure the handoff and recovery effort inherent in replacement.
Declare correction scenarios, repetitions, order balance, rubric, quality and
preservation gates, material improvement, and acceptable overhead before
trials. Include naturally occurring no-correction cases; do not create a
problem to force a correction. A paired controlled case with the same artifact
and finding can compare first-correction handling.

Measure first-correction acceptance, violations by stage and severity,
omissions or stale instructions, correctness and preservation, correction
rounds, repeated reading or checks, human steering, handoff plus review time,
and context recovery or setup. Record cost if available, otherwise unknown;
do not assume a cache advantage.
Recommend continuity, replacement per exchange, a conditional approach, no
change, or an inconclusive result. This plan authorizes no trial or policy
change.

## Acceptance

- **AC-1 TODO** The protocol isolates correction-session continuity within a
  Work, defines both conditions and their information boundaries, matches the
  listed controls, and predeclares scenarios and thresholds.
  Validation: inspect paired handoffs and a natural no-correction case.
- **AC-2 TODO** Evidence records report first-correction acceptance, violations,
  omissions, preservation, corrections, steering, review time, recovery effort,
  repeated work, and cost availability.
  Validation: trace both conditions to the declared measures, including a
  paired artifact/finding where available.
- **AC-3 TODO** The recommendation follows its predeclared basis, notes
  limitations, allows no-change or inconclusive results, and does not imply
  trial authorization or policy adoption.
  Validation: compare the conclusion with the evidence, thresholds, and
  existing guidance and authorization route.

Follow [Investigation guidance](../../../../../workflow.md#investigations).
