# Leaf-agent selection protocol

**Status:** frozen draft pending independent review and integration. The two
fixtures, prompts, source identities, current guidance/tool base, replay
commands, reviewer assignment, and environment are specified below and in the
fixture contracts. No trial is authorized or has run.

## Design

Compare three leaf conditions on two bounded fixtures: A = GPT-6 Luna low
(current baseline), B = GPT-6 Luna medium, and C = GPT-6.1 Sol low. Run 18
fresh sessions in total: two fixtures × three conditions × three repetitions.
Run them sequentially, with one isolated worktree from the same frozen fixture
revision for each session. Record and freeze fixture execution order before
dispatch. Do not reuse conversation context, artifacts, or branches between
runs. Use the exact current guidance and tools at runtime base
[`f7e03b6`](https://github.com/msitarz/ataraxia/commit/f7e03b6237ac240b41e784d1e9cdd4dac1118ccd).
Within each fixture, keep the owning parent, executor prompt, setup, checks,
and expected outcomes fixed for its nine runs; change only the model/effort
condition. Each run gets an isolated worktree at that same base, with only the
fixture-specific input preparation documented in its owning-parent-only
section.

For each fixture, use the same order rotation:

| Repetition | Condition order |
| --- | --- |
| 1 | A, B, C |
| 2 | B, C, A |
| 3 | C, A, B |

The same owning parent dispatches directly to the leaf and independently
reviews each initial and corrected artifact. The owning parent/reviewer is
root Codex in the authorizing session, GPT-6; reasoning effort is not exposed
here and is therefore unknown. Keep the same reviewer identity and available
model/effort throughout; do not silently reset or substitute the reviewer.
Apply the same frozen rubric without condition labels where practical. Full
blinding may not be possible because the parent dispatches each setting and
runs are sequential. For each review, record whether labels were hidden and
which settings and prior results the parent knew. Do not introduce another
reviewer.

## Review and correction

Evaluate the initial artifact before corrections. Record first-artifact
acceptance and findings by severity:

- **Blocking:** correctness, preservation, scope, or a required check fails.
- **Material:** a required outcome is missing or needs correction, but can be
  fixed within the assigned scope.
- **Minor:** a non-blocking clarity or presentation issue.

The rubric and fixture-specific preservation inventories are defined in the
two fixture contracts and must be checked against the integrated evidence
commit before dispatch. Send one consolidated finding set to the same leaf
session per correction round. Allow at most two rounds. Stop before another
round if it repeats an earlier finding; also stop when the second round ends
without all required gates passing. Record the run as failed or incomplete
under the frozen rubric. A stalled run follows the existing orchestrator
stop-and-report rule and consumes its dispatch; do not dispatch a replacement.

An initial artifact is accepted unchanged when it passes the correctness,
preservation, scope, and check gates without blocking or material findings.
Minor findings may be recorded without requesting a correction.

## Measures and boundaries

For every run, record condition, fixture revision, order, dispatch time, initial
artifact time, each review/correction exchange, final review time, and final
gate outcomes. End-to-end time starts at dispatch and ends when the owning
parent completes final review; it includes executor and wait time. Separately
record the parent's active review minutes, first-artifact acceptance, finding
counts by severity, correction rounds, human steering, and whether checks
were reused or repeated. Record token/cost values only if available; otherwise
mark them unknown, never zero. Record protocol deviations and missing
measurements. Report protocol/fixture preparation effort separately from the
18 run results.

## Decision rule

Summarize each fixture separately using initial-acceptance counts, median and
range of end-to-end time, correction burden, severity findings, gate failures,
and missing values. Do not pool documentation and code times. A candidate can
be recommended for a broader comparison in that same task class only when all
nine final artifacts for the fixture pass correctness, preservation, scope,
and required-check gates, and either:

1. its initial acceptance count is at least two additional accepted initial
   artifacts out of three compared with Luna-low, with median end-to-end time
   no more than 25% higher; or
2. its median end-to-end time is at least 20% lower, with no worse initial
   acceptance count or total correction rounds than Luna-low.

Otherwise retain Luna-low for now or report the fixture result as
inconclusive. Mixed, incomplete, or protocol-invalid evidence is inconclusive.
Even a passing result supports only a broader comparison in the same task
class; it does not support a global default or policy change. The owning parent
will apply this rule as written and report per-fixture medians, ranges, and
failures; no cutoff may be changed after seeing results.

## Frozen inputs and authorization request

The documentation fixture uses `doc/orchestrator.md` blob
`cd886039148f5c3af1d8adf6aeed42c2443a1909` at runtime base f7e03b6. It is a
different task and source blob from the earlier prose trial. The code fixture
uses runtime base f7e03b6 with only `src/ataraxia/provider.py` and
`test/unit/test_provider.py` restored to their exact f4eddb1 historical blobs.
Its overlay command, blob identities, reference-only evidence, and verified
checks are in the code fixture contract. This keeps modern guidance, Make
targets, and locked tools while replaying the historical task inputs.

Before dispatch, prepare each fresh worktree from the integrated f7e03b6 base.
For documentation, verify the exact doc blob before handoff. For code, apply
the documented two-file overlay, verify exactly those two paths differ, and
verify their exact historical blobs. Use `UV_PYTHON=3.14.7` for setup and all
18 worktrees; stop if that interpreter or the locked f7 setup is unavailable.
The preparation probe passed `make verify-setup`, focused provider tests (6
passed), focused lint and format checks, and `make typecheck` on this exact
overlay. Run each fixture's declared checks against every trial artifact.

Leaf handoffs contain only that fixture's exact executor prompt and the
prepared tree. Never provide the full fixture file, parent-only sections,
commit references, historical patches, or other reviewer answers. Instruct
the leaf not to inspect Git history, refs, or tags; the owning parent prepares
the input overlay without exposing its source. This is necessary because the
repository history contains the expected code change. Record the prepared
tree's input identities and setup evidence in the run record.

**Authorization request to make after independent review and integration:**
authorize exactly 18 sequential, fresh leaf dispatches: two fixtures
([documentation](fixtures/documentation.md) and [code](fixtures/coding.md)) ×
GPT-6 Luna low, GPT-6 Luna medium, and GPT-6.1 Sol low × three repetitions,
using the rotations above, the frozen f7e03b6 runtime/guidance base, the exact
fixture inputs and prompts, isolated worktrees, and the fixed owning-parent
reviewer described here. No replacement dispatches are allowed. Preparation
effort is reported separately; trial parent active review time is measured,
but total expected human effort is not yet measured and remains unknown.
Token/cost measurement availability is unknown; record unavailable values as
unknown. The required Python and locked-tools setup is available in the
preparation probe, but recheck availability at launch. This request is not
authorization: do not dispatch until the evidence commit is independently
reviewed and integrated and a maintainer explicitly authorizes this exact
bounded request.
