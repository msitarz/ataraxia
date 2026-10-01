# Guidance application

## Question

What helps orchestrators apply existing guidance consistently in fresh and
long-running sessions? Recent work read the handoff-brevity rule yet repeated
policy and produced an oversized guidance-editing Work. Distinguish discovery,
interpretation, application, and review failures. The
[parent Work](../README.md#works) links findings and coordinates related
owner changes.

The first two bounded model/effort batches are recorded in the
[prose trial report](prose-trial.md). All four executors were fresh; these
trials do not satisfy AC-2's fresh-versus-long-session or intervention
comparison. All Investigation criteria remain TODO.

## Comparison

Compare the current guidance and independent-review baseline with consultation
at decision boundaries, existing mechanical/tool-permission enforcement where
available, and explicit review of guidance compliance. Assess each candidate's
fit, tradeoffs, and uncertainty; do not assume unavailable tools exist.

Use comparable bounded tasks in fresh and long-running sessions. Keep task
scope, applicable guidance, agent/model and effort, and available tools
comparable; vary the declared intervention, including reviewer focus for the
compliance-review candidate. Before trials, declare the baseline, evaluation
basis, material improvement threshold, acceptable overhead, and
requirement-preservation criteria. Treat session age as a condition; do not
attribute differences to it alone.

Record violations and corrections by failure stage; repeated instructions,
checks, and PR-description edits; elapsed time to a reviewable artifact;
reviewer effort; consultation or enforcement overhead; requirement
preservation; and limitations or confounds. Report counts and timings
consistently across conditions. Recommend a change, no change, or an
inconclusive result.

## Acceptance

- **AC-1 TODO** The protocol distinguishes discovery, interpretation,
  application, and review failures; compares the baseline with the three
  candidates; and declares its evaluation basis before trials.
  Verification: classify the known read-but-violated handoff-brevity rule and
  review that missed its repeated explanations by failure stage.
- **AC-2 TODO** Comparable fresh and long-running trials report the specified
  violation, correction, repetition, elapsed-time, reviewer-effort, overhead,
  preservation, and limitation evidence.
  Verification: compare the trial records against the declared controls and
  measurement set for both session conditions.
- **AC-3 TODO** The recommendation follows the evidence and stated basis,
  permits no-change or inconclusive outcomes, and does not itself adopt policy.
  Verification: compare the recorded recommendation with the evidence and
  thresholds declared before the trials.

Follow [Investigation guidance](../../../../../workflow.md#investigations),
the existing [documentation review owner](../../../../../README.md#review),
and [orchestrator guidance](../../../../../orchestrator.md). Coordinate with
the mapped [handoff, PR-evidence, tree, and editing Works](../README.md#works)
when recommendations touch their owners; avoid duplicating their contracts.
