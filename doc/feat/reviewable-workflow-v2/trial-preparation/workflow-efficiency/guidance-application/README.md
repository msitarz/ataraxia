# Guidance application

## Question

What helps orchestrators apply existing guidance consistently in fresh and
long-running sessions, and what change, if any, is supported by evidence?
Recent work read the existing handoff-brevity rule yet repeated policy and
produced an oversized guidance-editing Work. Distinguish discovery, rule
interpretation, application, and independent-review failures; do not assume
session length caused the result. The
[parent Work](../README.md#works) records the observations and coordinates
related owner changes.

## Comparison

Compare the current guidance and independent-review baseline with three
candidates: consultation with the relevant owner at decision boundaries;
mechanical or tool-permission enforcement where an existing capability allows
it; and explicit review of compliance with the applicable guidance. For each,
assess fit, tradeoffs, and what remains uncertain. Do not propose new tooling
as though it already exists.

Plan comparable bounded tasks in fresh and long-running orchestrator sessions.
Hold task scope, applicable guidance, agent/model and effort, available tools,
and reviewer focus constant where practical; use matched tasks or alternate
conditions to separate session state from task differences. Before trials,
declare the baseline, evaluation basis, material improvement threshold,
acceptable overhead, and requirement-preservation criteria. Treat session
length as a condition to compare, not a causal explanation by itself.

Record discovery, interpretation, application, and review violations and
corrections; repeated instructions, checks, and PR-description edits; elapsed
time to a reviewable artifact; reviewer effort; consultation or enforcement
overhead; whether substantive requirements were preserved; and limitations or
confounds. Report counts and timings consistently across conditions. The
Investigation recommends a change, no change, or an inconclusive result; it
does not adopt policy automatically.

## Acceptance

- **AC-1 TODO** The protocol distinguishes discovery, interpretation,
  application, and review failures; compares the baseline with the three
  candidates; and declares its evaluation basis before trials.
  Verification: inspect the protocol and classify a missed owner rule and an
  applied rule that is later rejected in review.
- **AC-2 TODO** Comparable fresh and long-running trials report the specified
  violation, correction, repetition, elapsed-time, reviewer-effort, overhead,
  preservation, and limitation evidence.
  Verification: compare the trial records against the declared controls and
  measurement set for both session conditions.
- **AC-3 TODO** The recommendation follows the evidence and stated basis,
  allows no-change or inconclusive outcomes, and does not treat session length
  as causal without supporting controls or adopt policy by itself.
  Verification: review the candidate comparison, uncertainty, and conclusion
  against the predeclared evaluation basis.

Follow [Investigation guidance](../../../../../workflow.md#investigations),
the existing [documentation review owner](../../../../../README.md#review),
and [orchestrator guidance](../../../../../orchestrator.md). Coordinate with
the mapped [handoff, PR-evidence, tree, and editing Works](../README.md#works)
when recommendations touch their owners; avoid duplicating their contracts.
