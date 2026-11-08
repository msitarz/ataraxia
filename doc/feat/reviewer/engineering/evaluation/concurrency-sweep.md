# Prospective C concurrency feasibility sweep

Read when preparing or interpreting this bounded follow-up to the
[retained C telemetry](../../../../../output/reviewer-evaluation/c-full-001/telemetry/telemetry.md).
This supplement belongs to the existing [Evaluation](README.md). It asks which
of concurrency 1, 5, 10 and 25 gives useful reliable throughput on a fixed small
C workload at `gpt-6-luna`, high effort. It does not measure classification
quality, replace the complete C comparison, or adopt a production setting.

## Authority and preparation boundary

The maintainer authorized terminal preparation and a PR for this prospective
600-call design. Preparation makes no model, neutral, baseline, or quota calls.
Independent definition and implementation review, a frozen manifest, and
explicit future execution and reconciled budget authorization are required
before launch. A PR, merge, executable launcher, or dry run grants no execution
authority. The Evaluation's acceptance criteria remain TODO.

Preparation delivers a public selected-pair manifest, exact ordered run
manifest, offline estimates, a terminal dry run and reproducible invocation,
preflight and fresh-output handling. Retain the preparation revision and checks.
Execution handoff names the maintainer or external operator who launches and
maintains the run, its evidence destination, authorized bounds, and how
observations return for analysis. Stop after preparation; no agent must remain
alive during execution.

## Frozen matched workload

Reuse the existing [C shared, rule and function inputs](inputs/c-preparation.md)
and `preparation/min.md` byte for byte. Do not create another prompt or copy 50
function files. Preserve the original corpus and private references. Selection
uses only public identities and sizes, never private labels, prior responses,
quality scores, or outcome-based tuning. No private file is needed for this
sweep.

Select exactly 50 distinct rule/function pairs from the public
[C manifest](inputs/c-manifest.json), using this deterministic method:

- Use rule order R1, R3, R4 and source-file order dispatch, planning, ledger.
- Allocate pairs per file as R1: 6/6/5, R3: 6/5/6, R4: 5/6/5; totals are
  17/17/16 per rule and 17/17/16 per file.
- Within each rule/file group, sort eligible pairs by composed prompt UTF-8 byte
  count, then qualified function name. For zero-based rank `i` among `n` pairs,
  assign size bin `floor(3*i/n)` (small, middle, large).
- Within each bin sort by SHA-256 of UTF-8 `rule ID`, LF, source-file ID, LF,
  qualified function name, with the identity tuple as tie breaker. Repeatedly
  visit small, middle, large, taking the next unselected pair until the group's
  allocation is met; skip exhausted bins. Refuse insufficient inventory.
- Order the selected calls by rule ID, source-file ID and qualified function
  name. Freeze this identical input order for all 12 blocks.

The public manifest records the algorithm/version, source revision, selected
identities, paths and SHA-256 digests of every consumed file, prompt digest and
byte count, size bins, and selection order. Verify all digests before each
block. This intentionally varied workload has transparent file/rule coverage and
context sizes; it is neither random sampling nor evidence of representativeness.

Use the existing `RepositoryReader` and `PlanBuilder` ports, following the
existing B caller's filtering approach where suitable. The caller selects paired
calls; independently filtering rule and function directories must not
accidentally expand 50 pairs into a Cartesian product. Preserve ordinary prompt
composition, input snapshots, identities and accounting. Offline preparation
must reconstruct the same selected plan for evidence inspection and reporting.
If existing inspection cannot reproduce a caller-selected plan, resolve that
narrow caller integration before declaring readiness; do not introduce a new
planning framework.

## Conditions and execution bounds

Each of four concurrency levels has three fresh 50-call blocks: 600 calls and
600 attempts total, with the same input order, model and effort in every block.
Use this predeclared block order, one block active at a time:

| Repetition | Concurrency order |
| --- | --- |
| 1 | 1, 5, 10, 25 |
| 2 | 5, 10, 25, 1 |
| 3 | 10, 25, 1, 5 |

Three rotations over four levels cannot perfectly balance order or carryover;
report this limitation. Do not reorder from observed performance. Use fresh
sessions and fresh per-block output directories, with no resumed or cached
answers. Avoid other Codex account usage where practical and record any overlap.
Retain host CPU/load, network conditions, provider/account activity when known,
UTC block times and cache/usage observations; unknown conditions remain unknown.

Record the actual system CLI executable path and `codex-cli 0.166.0` version
before launch and every block; do not install or pin another binary. Abort on
version, model/effort, input, settings or boundary drift. Retain the actual
invocation and declared tools/context under the
[accepted CLI boundary](protocol.md#cli-invocation-boundary-and-accepted-limitation).
That limitation does not waive immutable-input, read-only, private-reference or
prior-answer protections. Unexpected tool activity or contamination stops the
sweep and remains retained evidence, not a valid observation.

Use 300 seconds per call, 10 seconds cleanup and 1 MiB combined output per
attempt. Harness retries and capacity retries are both zero. No quota probes,
refills, automatic reruns or automatic quota polling/resumption are permitted.
Codex's internal transport recovery remains enabled as in C, retained and
measured separately from harness attempts. It does not create a second harness
attempt or prove a physical transport-attempt count.

Cancellation, unsafe or uncertain cleanup, quota exhaustion, version/boundary
drift, or a failed block stops all subsequent blocks. A failed block means
incomplete dispatch/accounting, unsafe cleanup, or fewer than 49 public-valid
responses. An isolated invalid response is retained and does not trigger refill.
Use the existing supervisor stop/cleanup guarantees; retain every planned but
undispatched slot as not started. Any later restart needs owner review and new
explicit authority; preserve the failed observations and declare the deviation.

## Prelaunch refusal and budget reconciliation

Before launch, print per-block and 600-call supplied-input token estimates,
estimator/version and excluded automatic context/output, prompt bytes, fixed
instruction estimates, output capacity, maximum attempts and elapsed capacity.
Token estimates are not actual usage, cost, or a token-budget guarantee. The
serial execution-plus-cleanup capacity is 51 hours 40 minutes at the bounds;
wave capacity across this schedule is 201 waves, or 17 hours 18 minutes 30
seconds at 310 seconds per wave, excluding launch, preparation and other
overhead. These are capacity calculations, not predictions or guaranteed wall
times. The combined per-attempt output cap allows up to 600 MiB before evidence
overhead.

The original 48-call/208-attempt and 40-hour limits do not authorize this sweep;
neither does the separate 2,232-call C authorization. The future execution
approval must explicitly cover these 600 calls/attempts and reconcile token,
money, wall-time and evidence-storage ceilings with the estimates. Refuse
missing or insufficient authorization or bounds before dispatch. No private
grading, reference adjudication or label budget is consumed by this follow-up.

## Public validity, metrics and decision rule

A public-valid response is a successfully completed, safely cleaned-up call with
exactly the declared C schema and its expected public rule/file/function
identity, one allowed assessment, and no duplicate, stale, foreign or missing
output. Use the existing public validation without loading private references.
PASS, VIOLATION, UNKNOWN and NOT_APPLICABLE are structurally valid assessments;
validity does not establish correctness or useful semantic quality.

A concurrency level is reliable only if **every** repetition yields at least
49/50 public-valid responses (98%) and no boundary or cleanup failure. Retain
all invalid and terminal-error counts and reasons. Do not select a winner from
speed alone or hide failed blocks behind an aggregate success rate.

For each block measure public-valid responses per minute from terminal launcher
start immediately before invoking that block through completed evidence writing
and cleanup. Record those endpoints and duration explicitly. This includes
startup and cleanup and differs from the old C telemetry's earliest-process to
latest-process window. Keep the old process-window rate separately if useful;
do not compare the two as equivalent throughput measures.

Compare matched repetition blocks. For each reliable level, take the median of
its three whole-block valid-response rates. Recommend the lowest concurrency
whose median is at least 90% of the best reliable median. Report all three rates
and paired rate ratios against the best-median level. If no level is reliable,
blocks remain incomplete, or the nominated lower level falls below 90% of that
level in any matched repetition, report the choice as inconclusive. This is a
practical screen with three repetitions, not a statistical equivalence claim.

Report per-block and per-level public validity, p50/p95 call elapsed latency,
reconnect/fallback occurrence and affected-call rates, terminal errors, raw
usage categories with known/missing counts, and observed process overlap. Use
the retained telemetry percentile and overlap methods where applicable. Keep
cached input within input and reasoning within output; do not double count or
infer cost from elapsed time. Report network instability and recovery side
effects alongside throughput even when the reliability threshold passes.

Timing includes startup and internal recovery; process overlap is not inference
parallelism. Make no claim about provider queue time, inference time, account
capacity, subscription limits, causal network effects, or classification/vote
quality. Retain raw observations, manifest, launcher timestamps, failures,
deviations, confounds and analysis. Results can support a bounded concurrency
recommendation; they cannot complete the broader Evaluation or adopt policy.

## Prepared terminal invocation

From a clean checkout of the reviewed preparation revision, run the offline
manifest check and dry run:

```sh
.venv/bin/python -m script.reviewer_eval.sweep_manifest --check
.venv/bin/python -m script.reviewer_eval.concurrency_sweep
```

The dry run makes no CLI binding, model, or quota calls. Future execution
requires a separate explicit authorization covering all 600 attempts and
reconciled planning, wall-time and evidence-storage bounds. The operator must
replace each placeholder with the authorized value and select a fresh external
output path whose parent exists:

```sh
.venv/bin/python -m script.reviewer_eval.concurrency_sweep --execute --authorized-600-calls --output /absolute/external/fresh-directory --supplied-input-token-planning-ceiling TOKEN_COUNT --wall-seconds SECONDS --evidence-bytes BYTES
```

The launcher checks the clean actual HEAD, input and manifest digests, system
CLI path and version, and remaining deadline before each block. It records the
launcher and manifest digests and retains block streams and timing in the
external root. It checks observed tool activity after each block; calls already
dispatched within that block may have run before detection. It stops before the
next block on unexpected activity. Evidence size and free storage are checked
between blocks while reserving the remaining output caps; evidence overhead can
exceed the ceiling during an active block. A later restart needs new authority.
The supplied-input planning ceiling covers only that proxy, not actual usage;
future approval must reconcile automatic context and output separately. The wall
bound must cover 201 scheduled waves plus 600 seconds of overhead; neither is a
wall-time prediction. Supplied input token estimates use the C byte-per-four
planning proxy and exclude automatic context and output; subscription cost and
actual usage remain unknown until observed. Record any known account activity,
network conditions, or cache observations alongside the retained evidence.
