# Leaf-agent selection protocol draft

**Status:** provisional scaffold. This records the agreed comparison design;
the fixtures, prompts, guidance/tool snapshots, reviewer assignment, and
environment have not been frozen. No trial is authorized or has run.

## Design

Compare three leaf conditions on two bounded fixtures: A = Luna low (current
baseline), B = Luna medium, and C = Sol low. Run 18 fresh sessions in total:
two fixtures × three conditions × three repetitions. Run them sequentially,
with one isolated worktree from the same frozen fixture revision for each
session. Record and freeze fixture execution order before dispatch. Do not reuse
conversation context, artifacts, or branches between runs. Use one guidance
snapshot and available toolset throughout. Within each fixture, keep the owning
parent, executor prompt, setup, and check commands and expected outcomes fixed
for its nine runs; change only the model/effort condition.

For each fixture, use the same order rotation:

| Repetition | Condition order |
| --- | --- |
| 1 | A, B, C |
| 2 | B, C, A |
| 3 | C, A, B |

The same owning parent dispatches directly to the leaf and independently
reviews each initial and corrected artifact. Apply the same frozen rubric
without condition labels where practical. Full blinding may not be possible
because the parent dispatches each setting and runs are sequential. For each
review, record whether labels were hidden and which settings and prior results
the parent knew. Do not introduce another reviewer.

## Review and correction

Evaluate the initial artifact before corrections. Record first-artifact
acceptance and findings by frozen severity. The draft severity scale is:

- **Blocking:** correctness, preservation, scope, or a required check fails.
- **Material:** a required outcome is missing or needs correction, but can be
  fixed within the assigned scope.
- **Minor:** a non-blocking clarity or presentation issue.

The exact rubric and the preservation inventory for each fixture must be
reviewed and frozen before dispatch. Send one consolidated finding set to the
same leaf session per correction round. Allow at most two rounds. Stop before
another round if it repeats an earlier finding; also stop when the second round
ends without all required gates passing. Record the run as failed or incomplete
under the frozen rubric. Do not dispatch a replacement session.

An initial artifact is accepted unchanged when it passes the correctness,
preservation, scope, and check gates without blocking or material findings.
Minor findings may be recorded without requesting a correction.

## Measures and boundaries

For every run, record condition, fixture revision, order, dispatch time, initial
artifact time, each review/correction exchange, final review time, and final
gate outcomes. End-to-end time starts at dispatch and ends when the owning
parent completes final review; it includes executor and wait time. Separately
record the parent's active review minutes, first-artifact acceptance, finding
counts by severity, correction rounds, human steering, and whether checks were
reused or repeated. Record token/cost values only if available; otherwise mark
them unknown, never zero. Record protocol deviations and missing measurements.
Report protocol/fixture preparation effort separately from the 18 run results.

## Draft decision rule

Summarize each fixture separately using initial-acceptance counts, median and
range of end-to-end time, correction burden, severity findings, gate failures,
and missing values. Do not pool documentation and code times. A candidate can
be recommended for a broader comparison in that same task class only when all
nine final artifacts for the fixture pass correctness, preservation, scope,
and required-check gates, and either:

1. its initial acceptance rate is at least two of three runs higher than
   Luna-low's (at least two additional accepted initial artifacts out of three,
   a two-thirds absolute-rate difference), with median end-to-end time no more
   than 25% higher; or
2. its median end-to-end time is at least 20% lower, with no worse initial
   acceptance count or total correction rounds than Luna-low.

Otherwise retain Luna-low for now or report the fixture result as
inconclusive. Mixed, incomplete, or protocol-invalid evidence is inconclusive.
Even a passing result supports only a broader comparison in the same task
class; it does not support a global default or policy change. The rule and
interpretation must be confirmed before the fixture revisions are frozen.

## Freeze and authorization gates

Before any dispatch, the owning parent must complete and review the provisional
fields in both fixture files: exact base and reference revisions, task scope,
executor prompt, preservation inventory, check commands, reviewer identity,
guidance/tool versions, and setup compatibility. The code fixture's historical
change and reference commit must be verified; do not copy its patch or expose
reviewer-only material to leaf sessions. Copy only the `Executor-facing draft`
section into each handoff; never pass the full fixture file. Add immutable
commit permalinks for verified reference evidence rather than copying
historical assets. Confirm that all 18 clean worktrees can use the same locked
environment and tools.

After freeze, prepare an explicit maintainer authorization request naming the
two fixture revisions, all three conditions, 18-session cap, fixed owning
parent/reviewer, run order, expected preparation and review effort where
available, and unknown costs or unavailable tools. Do not dispatch until the
protocol evidence is reviewed and integrated and that exact request is
explicitly authorized. This scaffold itself grants no authorization.
