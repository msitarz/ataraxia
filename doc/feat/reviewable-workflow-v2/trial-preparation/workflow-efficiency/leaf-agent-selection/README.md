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

## Works

- **DONE**
  [Frozen protocol and replay fixtures at evidence revision `3867c58`](https://github.com/msitarz/ataraxia/commit/3867c58):
  bounded documentation and code fixtures, matched conditions, review and
  preservation gates, measures, thresholds, and an authorization request. No
  trial runs in this Work.
- **DONE** [Controlled comparison](controlled-comparison/README.md), with
  [results](controlled-comparison/results.md): the completed authorized
  comparison recommends only a broader coding comparison after input isolation
  and prompt/rubric alignment; Luna-low remains the default.

The current Luna-low default and direct parent-to-leaf topology remain in force
throughout this Investigation. The reviewed protocol and fixture inputs are
preserved at
[evidence revision `efdc21a`](https://github.com/msitarz/ataraxia/commit/efdc21a1316fd381d29ab5002bd818233e7fbb43).
That evidence was integrated at master `617fe22`; the maintainer authorized the
18-run comparison, whose results and raw evidence are in
[results](controlled-comparison/results.md). No policy change is adopted here.

## Comparison

The preserved protocol and fixtures at evidence revision
[3867c58](https://github.com/msitarz/ataraxia/commit/3867c58) own the evaluation
method. The comparison varies only the model/effort condition where possible
and records remaining confounds. It includes first-artifact acceptance,
correctness and
requirement preservation, correction rounds, elapsed time through parent
review, separate parent review effort, human steering, check reuse, and token
or cost availability. Unavailable values remain explicitly unknown. The
decision rule permits only a threshold-supported recommendation; otherwise it
retains the default or reports an inconclusive result.

This Investigation recommends but does not adopt policy. A consequential
change must follow the authoritative owner and
[WDR lifecycle](../../../../../wdr-workflow.md), with maintainer approval.

## Acceptance

- **AC-1 DONE** The protocol defines representative documentation and code
  fixtures, matched conditions, repetitions and order, quality and preservation
  gates, review rubric, measurements, material-improvement and overhead
  thresholds, correction and stall handling, and a bounded authorization
  request before execution.
  Verification: inspect the frozen protocol and fixture revisions against both
  task classes and all three model/effort conditions.
- **AC-2 DONE** Trial results account for first-artifact acceptance,
  correctness and preservation, correction rounds, executor and parent effort,
  time through parent-reviewed artifact, human steering, check reuse, and
  token/cost availability for each condition.
  Verification: trace every measure and unavailable value in the results to
  the frozen protocol.
- **AC-3 DONE** The recommendation follows the declared basis, distinguishes
  evidence from uncertainty, permits default/no-change or inconclusive
  outcomes, and does not imply policy adoption or authorization for further
  model/effort changes.
  Verification: compare the conclusion with the trial evidence, the current
  Luna-low default, and the owner/WDR approval path.
