# Protocol and fixture

Freeze a separate, bounded documentation task and a matched direct-versus-
orchestrated comparison for the parent [Investigation](../README.md). This
Work prepares the trial; it does not dispatch sessions or claim results.

## Fixture

The standalone Work is [fixture/README.md](fixture/README.md), with source facts
in [fixture/facts.md](fixture/facts.md) and a deliberately repetitive starting
document in [fixture/guide.md](fixture/guide.md). Its repository-root-relative
file path is
`doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/single-agent-execution/protocol-and-fixture/fixture/README.md`.
It requires edits to `guide.md` only. Direct and control executors receive the
identical tree and task prompt at one frozen Git commit; this Investigation is
not part of the fixture. Use independent disposable worktrees at that commit,
with repository root as CWD.

## Trial protocol

Run three pairs sequentially and randomize which condition goes first within
each pair (record the coin flips or seed). Each pair
has one fresh direct Luna-low executor and one fresh Luna-low orchestrator with
one fresh Luna-low executor: nine agent sessions total. All nine use the same
model and effort. The orchestrator reviews its executor's return. No nested
delegation or context transfer. The control executor gets exactly the direct
executor prompt; the control orchestrator gets the same task plus the role
instruction below. Only the maintainer's explicit trial authorization can
start these sessions.

The following exact prompt is used for each direct executor and is forwarded
verbatim by each control orchestrator to its delegated executor:

> At snapshot `<FIXTURE_SHA>`, with repository root as CWD, execute
> `doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/single-agent-execution/protocol-and-fixture/fixture/README.md`.
> Read that Work, its sibling `facts.md`, `AGENTS.md`, `doc/change-rules.md`,
> `doc/README.md`, `doc/workflow.md`, and `doc/validation.md`. Run `make help`
> then `make setup` in this fresh workspace. Change only
> `doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/single-agent-execution/protocol-and-fixture/fixture/guide.md`;
> run
> `make doc-format ARGS=doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/single-agent-execution/protocol-and-fixture/fixture/guide.md`
> and `make doc-check`. Return the artifact, criterion evidence, check output,
> correction history, and these measures: self-reported engaged minutes
> (including setup/context reading, excluding known idle waits), dispatch-to-
> first activity and dispatch-to-final-artifact elapsed minutes, progress and
> human steering message counts, check runs/repeats, correction rounds/causes,
> and tokens/cost if visible or `unknown`. Mark unavailable measures `unknown`;
> never infer engaged minutes from elapsed time. Do not delegate or take PR,
> merge, ready-state, or policy actions.

**Control-orchestrator prompt:**

> Own scope and review for the fixture Work at snapshot `<FIXTURE_SHA>`, with
> repository root as CWD. Make exactly one handoff to a fresh Luna-low executor
> and forward the complete exact executor prompt above verbatim. Do not edit
> the fixture. Review the completed return, reuse its checks when inputs are
> unchanged, and report artifact, evidence, checks, corrections, your
> self-reported engaged minutes, dispatch-to-final-review elapsed minutes,
> progress/steering messages, and tokens/cost if visible or `unknown`. Mark
> unavailable measures `unknown`; never infer engaged minutes from elapsed
> time. Do not prepare its environment or run project checks. Take no PR,
> merge, ready-state, or policy actions.

Use three fresh workspaces per condition, each from the same snapshot with no
prepared environment; never share mutable environments between runs. The
control orchestrator and its executor share that run's workspace, but not
session history. Executors receive the same repository tree and necessary
guidance; do not give the direct executor parent-only messages or information
from another run. Count setup effort once per workspace. Keep the evaluator
independent of all nine sessions. Give it six `guide.md` files and check
evidence under randomized IDs, hiding condition and role when practical; record
any inference or other unblinding.
Every artifact is gated for the three required headings in order, accurate
coverage of every source fact, the original valid link, no unsupported rules,
edits limited to `guide.md`, and passing local Markdown checks.

The platform does not automatically expose engaged model time or human time.
Use participant self-reported engaged minutes; mark them unknown when
unavailable. Also record UTC dispatch, first activity, first artifact,
corrections, checks, and final-artifact timestamps to derive elapsed durations.
Elapsed time is not a substitute for engaged effort. Record workspace setup
separately; setup and context reading are included in self-reported engaged
minutes and tagged. Record human steering messages/minutes, progress messages,
check runs and repeats of unchanged inputs, correction rounds and causes,
artifact-ready wall time, per-role tokens/cost or `unknown`, and each gate
result. Keep one results row per run with its pair ID; no per-revision journal.
Count a correction round when someone requests a revision after a complete
draft. The independent evaluator scores final artifacts without sending
corrections to participants; record reviewer minutes separately. Combined
effort is executor plus orchestrator self-reported engaged minutes after
dispatch and human steering minutes; evaluator time remains separate. Human
minutes must be logged by the human or marked unknown. Tool-wait and context-
switch intervals may be imperfectly identified; disclose that limitation.
Stop measurement at the locally checked, reviewable artifact; no PR-ready or
live-CI phase applies. Local results do not replace full CI for any later PR.

A direct-execution win requires all three direct artifacts to pass every gate
and at least two of the three pairs to save both at least 15% and 10 combined
engaged minutes versus control. Compute savings as control minus direct and
divide by control for the percentage. In each qualifying pair, direct may add at
most one correction round and five steering minutes relative to its control run.
Example: control effort 80 minutes and direct effort 60 saves 25% and 20
minutes; the pair qualifies if the overhead limits also pass. Use only
comparable reported engaged-minute values. If a required value is unknown, that
pair cannot establish a win; if required values remain unavailable, the result
is inconclusive. Two qualifying pairs plus all three direct gate-passing
artifacts meet the rule. One qualifying pair is no win; any gate failure makes
the direct condition ineligible. Fewer than three complete pairs is
inconclusive. Report every pair, median and range, unavailable measures,
deviations, and quality findings. A result that misses the threshold keeps the
current topology or is inconclusive; it never adopts policy.

Proposed exact maintainer authorization (replace `<FIXTURE_SHA>` with the
retained evidence commit before requesting approval): “Authorize three
randomized pairs using fixture snapshot `<FIXTURE_SHA>`: exactly nine fresh
Luna-low sessions, consisting of three direct executors, three control
orchestrators, and three delegated control executors. Authorize only the three
control handoffs. No live PR, ready-state change, merge, or policy adoption is
authorized. Preserve independent evaluation and ordinary maintainer review.
This local trial is not CI evidence; any resulting PR requires full CI.” This
request is not authorization. Missing or mismatched revision, prompt, effort,
count, or condition is a stop condition.

## Acceptance

- **AC-1 DONE** A standalone documentation fixture, bounded prompt, and
  acceptance rubric are frozen at a revision and do not depend on this
  Investigation's completion.
  Verification: at the retained evidence revision, the standalone fixture and
  exact prompt name the frozen files and task. Temporarily reorganized
  `guide.md` under the required headings, retained all four facts and the local
  link, and changed no other fixture file; targeted formatting and
  `make doc-check` passed before restoring the starting fixture.
- **AC-2 DONE** The nine-session design, matched prompts and conditions,
  independent evaluation, measurements, per-run gates, denominator, and
  thresholds are explicit and locally reviewable.
  Verification: walked one hypothetical pair with control effort 80 and direct
  effort 60: the example arithmetic is 25% and 20 minutes saved, meeting the
  pair threshold only if overhead passes. Two qualifying pairs are required;
  unknown required values or fewer than three complete pairs cannot establish a
  win. No trial results are claimed.
- **AC-3 DONE** The protocol names the required authorization and preserves
  current delegation, review, maintainer, and CI boundaries.
  Verification: inspected the proposed dispatch text for three pairs/nine
  sessions, exactly three handoffs, no PR/merge/policy actions, independent and
  maintainer review, and full CI for any later PR. It explicitly states that
  the request grants no authority; no trial authorization or results are
  claimed.
