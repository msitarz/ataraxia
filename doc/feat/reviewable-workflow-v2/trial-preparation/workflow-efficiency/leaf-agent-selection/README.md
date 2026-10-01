# Leaf-agent selection

## Question

When should a leaf task use GPT-6 Luna at low or medium effort, or GPT-6.1 Sol
at low effort? The current default is Luna low. Existing authorization for
earlier comparisons does not authorize new agents or effort settings.

The [guidance-application Investigation](../guidance-application/README.md) asks
how agents apply guidance consistently. This Work asks which authorized
model/effort condition fits a task; its
[prose trial](../guidance-application/prose-trial.md) is preliminary evidence
from one documentation task, not a general selection recommendation.

## Comparison

Compare representative bounded documentation and code leaf tasks under
matched baseline, scope, guidance, tools, and session conditions. Declare task
classes, repetitions, same review rubric, quality and preservation gates,
material-improvement threshold, and acceptable overhead before trials. Vary
the model/effort condition only where possible and record remaining
confounds.

For each condition, assess first-artifact acceptance, correctness and
requirement preservation, correction rounds, elapsed time through reviewed
artifact including parent review, human steering, and check reuse. Record
token use or cost when available; otherwise mark it unknown and make no cost
claim. Conclude with a task-sensitive recommendation, the current default, or
an inconclusive/no-change result, distinguishing observed evidence from
uncertainty.

This Investigation recommends but does not adopt policy. A consequential
change must follow the authoritative owner and
[WDR lifecycle](../../../../../wdr-workflow.md), with maintainer approval.

## Acceptance

- **AC-1 TODO** The protocol defines representative documentation and code
  task classes, matched conditions, repetitions, quality/preservation gates,
  material improvement, acceptable overhead, and the review rubric before
  execution.
  Verification: inspect the declared protocol against an example of each task
  class and all three model/effort conditions.
- **AC-2 TODO** Trial results account for first-artifact acceptance,
  correctness/preservation, correction rounds, time through parent-reviewed
  artifact, human steering, check reuse, and token/cost availability for each
  condition.
  Verification: trace each measurement and unavailable value through the
  recorded results and compare it with the declared protocol.
- **AC-3 TODO** The recommendation follows the declared basis, distinguishes
  evidence from uncertainty, permits default/no-change or inconclusive
  outcomes, and does not imply policy adoption or authorization for further
  model/effort changes.
  Verification: compare the conclusion with the trial evidence, the current
  Luna-low default, and the owner/WDR approval path.
