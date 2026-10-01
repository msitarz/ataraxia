# Single-agent execution

## Question

For a bounded Work, does direct execution by one agent improve the path to a
reviewable artifact compared with the current orchestrator-to-executor
topology? This differs from the
[guidance-application Investigation](../guidance-application/README.md) on
compliance interventions and from
[leaf-agent selection](../leaf-agent-selection/README.md) on model and effort.

## Comparison

Compare genuinely fresh direct-agent runs with the existing direct
orchestrator-to-executor arrangement. Use the same self-contained Work
contract and an initial prompt resembling a maintainer's “execute this Work”
request; add only necessary branch context and novel constraints. Do not give
the direct agent privileged parent context. Existing read-only orchestration
and delegation rules remain in force; declare trial authorization before
execution. Do not exercise live PR or merge exceptions. The current direct
orchestrator-to-Luna-low leaf path remains the default; earlier trial
authorization does not authorize a new agent or effort.

For the primary topology comparison, keep implementing model and effort
comparable. If a realistic model mix is also assessed, report it separately;
different models cannot isolate topology effects. Hold task scope, guidance,
tools, and session freshness comparable. Use the same independent post-run
evaluator and maintainer CI gates. Direct-agent self-review does not count as
independent review.

Measure setup, runtime checks, progress messages, context reading, repeated
work, corrections, human steering, and time through the reviewable artifact.
Report executor and parent/orchestrator effort together, including the common
independent review. Record token use or cost when available; otherwise mark it
unknown. Declare task classes, repetitions, quality and preservation gates,
material improvement and overhead thresholds before runs. Recommend a
task-sensitive change, current topology, or inconclusive result; this
Investigation does not waive policy or model-authorization requirements.

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
