# Leaf-agent selection protocol and fixtures

Freeze the protocol and two bounded fixtures needed to compare Luna low, Luna
medium, and Sol low for leaf execution. This Work prepares an authorization
request; it does not dispatch trial agents or make a selection recommendation.

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

Before any run, the protocol must state exact repetitions per fixture and
condition, balanced or randomized run order, the common independent review
rubric, correctness and requirement-preservation gates, and the applicable
local checks. Identify one independent evaluator, separate from the owning
parent, to review every initial artifact and correction under that rubric; the
owning parent review is separately timed and included in end-to-end time.
Freeze severity levels and acceptance rules so all conditions receive the same
evaluation.

Predeclare first-artifact acceptance, correction rounds, evaluator and parent
effort, elapsed time from dispatch through parent-reviewed artifact, human
steering, check reuse or repetition, and token/cost availability. Define a
material-improvement threshold, acceptable overhead ceiling, and conservative
decision rule with numeric cutoffs and their rationale. The rule must account
for variation across task classes, require all quality and preservation gates
to pass, and allow only a supported conditional recommendation; otherwise
retain the default or report an inconclusive result. Missing token or cost
data is recorded as unknown, never as zero or as a basis for a cost claim.

Set a correction-round cap and handling for stalled work or a repeated
unresolved finding. Use consolidated reviewer findings and the existing
orchestrator stop-and-report rules. State whether an invalid or stalled run
blocks its matched comparison and whether a replacement is permitted within
the declared dispatch cap; do not improvise replacement runs after seeing
results. Record deviations and incomplete runs without treating them as
successful outcomes.

Conclude with an explicit authorization request that names the three exact
conditions, fixtures and revision, repetitions, total maximum dispatch count,
owning parent and independent evaluator, estimated human effort where
available, and unknown costs or unavailable capabilities. Ask for explicit
authorization for that bounded plan. The request itself does not authorize
execution. The protocol and fixture commit must be reviewed and integrated
before the controlled comparison begins.

## Acceptance

- **AC-1 TODO** Two replayable bounded fixtures are frozen: one documentation
  task and one code task, each with its exact revision, prompt, scope, expected
  outcome, guidance, tools, setup, and check policy.
  Verification: inspect both fixture definitions and confirm that each
  condition can use the same inputs.
- **AC-2 TODO** The pre-run protocol fixes the three conditions, direct
  parent-to-leaf topology, fresh sessions, matched controls, repetitions and
  balanced order, fixed independent rubric and evaluator, preservation and
  quality gates, correction/stall rules, measures, numeric improvement and
  overhead thresholds, and conservative decision rule.
  Verification: walk the protocol against both fixtures and a hypothetical
  passing, failing, and inconclusive outcome; confirm no result is needed to
  determine the rule.
- **AC-3 TODO** A bounded authorization request names the conditions, total
  dispatch cap, owning parent, independent evaluator, estimated effort and
  unknown costs, and makes clear that execution waits for reviewed integration
  and explicit maintainer authorization.
  Verification: inspect the request and confirm it grants no dispatch or policy
  authority by itself.

No measured result or policy change belongs in this Work. Keep the current
Luna-low default until a later reviewed decision follows the applicable WDR
path.
