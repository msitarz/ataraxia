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

## Trial protocol

Use a paired, randomized-order comparison. The experimental unit is one fresh
session completing the same frozen Work contract from the same base revision.
The primary condition is one direct Luna-low executor. The control is a
Luna-low orchestrator that delegates once to a fresh Luna-low executor, reviews
the completed artifact, and returns it. Keep implementation model and effort
equal in both conditions. Do not add nested executors. If a later question
tests another model mix or effort, run and report it as a separate experiment.

The first fixture is this Work itself: its README and parent entry as they
exist at base commit `26dd00b0d61956dd3cb4caafc21a4b825fe9a600`. Give both
conditions that exact tree and the same repository guidance routes, and ask for
a complete, reviewable Investigation protocol and parent-map update. This is a
documentation Investigation fixture; it does not establish results for code
Works or other task classes. Freeze a fixture manifest before dispatch with
the commit, Work path, prompt text, applicable guidance paths, tool access,
acceptance rubric, and any excluded data. Do not use this executor's completed
artifact as a starting point for one condition. Use disposable isolated
worktrees and fresh sessions so no session sees the other result or this
executor's private investigation context.

Run three pairs (six sessions), using a coin flip or recorded random seed to
choose which condition runs first in each pair. Each session starts from the
same base, with no shared session history, hidden review, or result from an
earlier run. The initial request is identical apart from its topology
instruction. For the direct condition, say: “Execute the Work at
`doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/single-agent-execution/README.md`
on base `26dd00b0d61956dd3cb4caafc21a4b825fe9a600`. Read the Work and its
applicable local guidance, make the smallest complete reviewable change, run
the relevant documentation check, and return the revision, criterion evidence,
checks, and any unrun checks or blockers. You own execution and may not
delegate. Existing maintainer review, merge, and CI gates apply.” For the
control, the orchestrator receives the same request with “You own scope and
review. Make one bounded handoff to a fresh Luna-low executor, then review and
return the artifact and evidence; do not implement the delegated change.” The
control executor receives the direct request and no parent-only context. The
maintainer must authorize the six fresh sessions and the control's delegation
before dispatch; this document and prior trial authorizations do not grant
that authority.

Before dispatch, the maintainer freezes a rubric requiring: all declared
protocol elements (matched conditions, fixture, repetitions/order, quality
gates, thresholds, measures, and exact authorization boundary); accurate
current-default and owner-policy statements; no unsupported performance claim;
valid local links and repository formatting; and no edits outside this Work
and its workflow-efficiency parent map. The same independent reviewer scores
all six artifacts without seeing the condition label until scoring is recorded.
Score criterion satisfaction pass/fail, preservation pass/fail, and review
effort in minutes. A failed acceptance or preservation gate cannot count as a
successful artifact even if it arrived quickly.

For each run, record UTC dispatch, first executor activity, artifact-ready,
checks-complete, independent-review-complete, and PR-ready timestamps. Report
wall time, executor active time, orchestrator active time, independent-review
minutes, and total active human-plus-agent minutes separately. In the delegated
condition, sum executor and orchestrator active time. Record human steering
messages and minutes, orchestration/handoff and context-reading minutes,
runtime checks and their time, repeated checks/work, correction rounds with
cause, first-review acceptance, preservation findings, and time to the
reviewable artifact. Capture token use and cost for each role when the platform
exposes them; otherwise write `unknown` per role and make no cost inference.
Count checks once per run, while marking a repeated check when the same
unchanged inputs were checked again. Keep one result row per run and report
each paired difference and the median and full range; do not keep a
per-revision journal.

Declare a material win only if one condition passes all six quality and
preservation gates and, in at least two of three pairs, reduces total active
human-plus-agent minutes through independent review by both 15% and 10 minutes,
with no increase greater than one correction round or five human-steering
minutes in either run of those pairs. A condition with a gate failure is not
eligible to win. If conditions trade time against quality, review effort, or
steering, or if fewer than three valid pairs finish, report the comparison as
inconclusive. These thresholds are decision aids for this small documentation
fixture, not a statistical claim. Even a measured win supports only a
recommendation to consider direct execution for comparable documentation
Investigations. It does not alter the authorized Luna-low leaf default,
delegate authority, review ownership, maintainer approval, merge control, or CI
gates. If total effort is tied within the declared threshold, retain the
current topology.

The current assigned session may prepare this protocol and fixture manifest,
but it is not a trial observation. Trial execution requires a separate,
explicit maintainer dispatch naming the six fresh sessions, the direct and
orchestrated topology assignments, Luna-low effort for every executor, the
frozen fixture commit and prompt, and authorization for one control
orchestrator-to-executor delegation. Dispatch must also state that no live PR,
ready-state change, merge, or policy adoption is authorized. Record results
only after independent evaluation and the ordinary maintainer and CI gates;
otherwise leave AC-2 unresolved and conclude that evidence is insufficient.

## Acceptance

- **AC-1 TODO** The protocol fixes one identical Work fixture and prompt at a
  pinned base, compares fresh direct Luna-low sessions with a one-handoff
  orchestrator-to-Luna-low path, randomizes pair order, and separates any
  model/effort comparison. No sessions have been dispatched.
  Verification: inspect the declared protocol and, after authorization, both
  initial handoffs for actual condition matching.
- **AC-2 TODO** Results include executor and parent effort, independent
  evaluation, checks, repeated work, corrections, steering, reviewable-artifact
  time, preservation, and available or unknown token/cost data.
  Verification: trace each trial result to the declared measures and gates.
- **AC-3 TODO** The recommendation is evidence-backed, reports limitations,
  and does not imply policy exceptions, agent authorization, or automatic
  adoption.
  Verification: compare the conclusion with declared thresholds, trial
  conditions, and existing owner/maintainer approval requirements.
