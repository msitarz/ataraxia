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

- **TODO** [Protocol and fixtures](protocol-and-fixtures/README.md): freeze
  bounded documentation and code fixtures, the matched protocol, review and
  preservation gates, measures, thresholds, and a bounded authorization
  request. No trial runs in this Work.
- **TODO** [Controlled comparison](controlled-comparison/README.md): after the
  protocol is reviewed and integrated, run only the Luna-low, Luna-medium, and
  Sol-low conditions with explicit maintainer authorization, then report
  evidence and a recommendation. No policy is adopted.

The current Luna-low default and the direct parent-to-leaf topology remain in
force throughout this Investigation. The controlled comparison cannot start
until the protocol child is integrated and the maintainer explicitly
authorizes its named conditions and bounded dispatch budget.
Integrate this revised parent plan before starting either child. The protocol
child still needs to settle exact fixtures, fixed reviewer, repetitions,
numeric thresholds, and the dispatch cap; this preparation records no trial
results or authorization.

## Comparison

The protocol child owns the fixtures and predeclared evaluation method. The
comparison varies only the model/effort condition where possible and records
remaining confounds. It includes first-artifact acceptance, correctness and
requirement preservation, correction rounds, elapsed time through parent
review, separate parent review effort, human steering, check reuse, and token
or cost availability. Unavailable values remain explicitly unknown. The
decision rule permits only a threshold-supported recommendation; otherwise it
retains the default or reports an inconclusive result.

This Investigation recommends but does not adopt policy. A consequential
change must follow the authoritative owner and
[WDR lifecycle](../../../../../wdr-workflow.md), with maintainer approval.

## Acceptance

- **AC-1 TODO** The protocol defines representative documentation and code
  fixtures, matched conditions, repetitions and order, quality and preservation
  gates, review rubric, measurements, material-improvement and overhead
  thresholds, correction and stall handling, and a bounded authorization
  request before execution.
  Verification: inspect the frozen protocol and fixture revisions against both
  task classes and all three model/effort conditions.
- **AC-2 TODO** Trial results account for first-artifact acceptance,
  correctness and preservation, correction rounds, executor and parent effort,
  time through parent-reviewed artifact, human steering, check reuse, and
  token/cost availability for each condition.
  Verification: trace every measure and unavailable value in the results to
  the frozen protocol.
- **AC-3 TODO** The recommendation follows the declared basis, distinguishes
  evidence from uncertainty, permits default/no-change or inconclusive
  outcomes, and does not imply policy adoption or authorization for further
  model/effort changes.
  Verification: compare the conclusion with the trial evidence, the current
  Luna-low default, and the owner/WDR approval path.
