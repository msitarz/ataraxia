# Leaf-agent selection protocol and fixtures

Freeze the protocol and two bounded fixtures needed to compare Luna low, Luna
medium, and Sol low for leaf execution. This Work prepares an authorization
request; it does not dispatch trial agents or make a selection recommendation.

The contracts are [protocol.md](protocol.md),
[fixtures/documentation.md](fixtures/documentation.md), and
[fixtures/coding.md](fixtures/coding.md). Their frozen inputs and replay
evidence passed independent review; integration and explicit maintainer
authorization remain pending. No trial is authorized or has run.

## Scope

Select one representative, bounded documentation task and one representative,
bounded code task. Record the exact fixture content and source revision, task
prompt, expected outcome, applicable guidance, tools and checks, and any setup
needed to replay each fixture. Use the same fixture revision and task prompt
for all conditions within each task class.

Freeze the current direct parent-to-leaf topology in every condition: the same
owning parent dispatches directly to a fresh leaf session, then reviews the
returned artifact and owns integration. Keep task, scope, guidance revision,
tools, setup, check policy, and reviewer conditions fixed; vary only the
declared model/effort condition where possible. Record remaining confounds.
Do not add a Sol wrapper, transfer session context, or change the Luna-low
default.

The protocol specifies repetitions, balanced order, a common owning-parent
review rubric, correctness and preservation gates, and checks. The same owning
parent, independent of each leaf executor, reviews every initial artifact and
correction. Measure parent review effort separately and include it in
end-to-end time. Apply the rubric without condition labels where practical;
otherwise record whether review was unblinded, which condition and prior
results the parent knew, and the resulting confounds.

Predeclare first-artifact acceptance, correction rounds, parent review effort,
elapsed time from dispatch through parent-reviewed artifact, human steering,
check reuse or repetition, and token/cost availability. Define a
material-improvement threshold, acceptable overhead ceiling, and conservative
decision rule with numeric cutoffs and their rationale. The rule must account
for variation across task classes, require all quality and preservation gates
to pass, and allow only a supported conditional recommendation; otherwise
retain the default or report an inconclusive result. Missing token or cost
data is recorded as unknown, never as zero or as a basis for a cost claim.

The protocol sets a two-round correction cap, handling for stalled work or a
repeated unresolved finding, and prohibits replacement dispatches. It uses
consolidated reviewer findings and existing orchestrator stop-and-report
rules. Record deviations and incomplete runs without treating them as
successful outcomes.

The protocol includes an explicit request for 18 dispatches across the three
exact conditions and two fixtures, fixed reviewer, and order. Preparation is
reported separately; expected total human effort and token/cost availability
remain unknown. It does not authorize execution. The controlled-comparison
contract links the replayable protocol and fixture assets at their evidence
revision. This child is removed by the separate cleanup commit after the
protocol evidence commit. The comparison itself remains blocked until that
evidence is integrated and a maintainer explicitly authorizes the 18-dispatch
request. Git preserves the evidence, so no second archive or tracking record is
needed.

## Acceptance

- **AC-1 DONE** Two replayable bounded fixtures are frozen: one documentation
  task and one code task, each with its exact revision, prompt, scope, expected
  outcome, guidance, tools, setup, and check policy.
  Verification: inspect both fixture definitions and confirm that each
  condition can use the same inputs.
- **AC-2 DONE** The pre-run protocol fixes the three conditions, direct
  parent-to-leaf topology, fresh sessions, matched controls, repetitions and
  balanced order, fixed owning parent/reviewer, rubric and label-blinding or
  unblinded-confound recording, preservation and quality gates, correction/
  stall rules, measures, numeric improvement and overhead thresholds, and
  conservative decision rule.
  Verification: walk the protocol against both fixtures and a hypothetical
  passing, failing, and inconclusive outcome; confirm no result is needed to
  determine the rule.
- **AC-3 DONE** A bounded authorization request names the conditions, total
  dispatch cap, fixed owning parent/reviewer, estimated effort and unknown
  costs; the replayable protocol and fixtures are preserved at an evidence
  commit and this sibling contract is updated with durable permalinks before
  cleanup.
  Verification: inspect the request and evidence links; confirm execution
  waits for reviewed integration and explicit maintainer authorization, and
  that the evidence remains reachable after protocol cleanup.

No measured result or policy change belongs in this Work. Keep the current
Luna-low default until a later reviewed decision follows the applicable WDR
path.
