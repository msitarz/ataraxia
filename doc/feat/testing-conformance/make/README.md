# Make testing boundaries

Preserve Make contracts with fast real-Make/fake-uv orchestration and selected
real-tool regressions. Follow [testing](../../../testing.md),
[integration guidance](../../../testing-integration.md), and
[test ownership](../../../test-ownership.md).

## Delivery map

- **DONE** Real-tool marker and optional filtering; default selection includes
  all.
- **DONE** Typed shared stub environment and isolated ordinary Make routing.
- **DONE** Typed isolated preparation and check execution orchestration.
- **DONE** Typed real-Git creation with isolated setup and retained-state
  checks.
- **DONE** Typed real-Git removal and pruning with refusal/read-only snapshots
  and retained files, refs, and registrations.
- **DONE** Disposable real-tool documentation checks/formatting with
  selected-file, exclusion, inbound-link, and read-only failure coverage.
- **DONE** Typed disposable acceptance selection and static declaration checks,
  with precise failures, neutral summaries, and no fixture-test execution.
- **DONE** Typed named size fixtures and disposable real-Ruff checks preserve
  clean/advisory/blocking boundaries at 25/26/50/51 statements.
- **DONE** [Matched baseline](matched-measurements.md) with frozen matched
  environments, retained eight-run evidence and separate selection medians.
- **DONE**
  [Final measurement attempt](matched-measurements.md#final-condition-stopped-comparison-inconclusive)
  stopped after a failed warm-up; comparison is explicitly inconclusive.
- **DONE** Isolated disposable process home/scratch outside repository
  snapshots, with deterministic cache-write regression and retained
  removal/pruning checks.
- **DONE**
  [Renewed final attempt](matched-measurements.md#corrected-final-renewed-attempt-stopped)
  stopped on a scratch-witness decoding failure; comparison is inconclusive.
- **DONE** Dedicated synthetic scratch witness survives real Git inspection,
  with complete repository snapshots and retained legitimate cache/witness data.
- **DONE**
  [Witness-final observations](matched-measurements.md#witness-final-observations-and-comparison)
  with eight successful invocations, separate medians and comparison limits.

Cleanup deliveries are complete;
[original baseline measurements](measurements.md) remain historical evidence.
Matched baseline and the inconclusive final attempt are delivered.
Scratch isolation, the stopped renewed attempt and witness correction are
delivered. Witness-final observations and selection medians are delivered;
parent integration and timing acceptance remain pending. Each complete leaf
diff must fit the
[five-minute review target](../../../workflow.md#scope-and-sizing); replan and
merge further splits before expansion.

Cleanup leaves preserve existing covers markers, add criterion-marked tests, and
precisely annotate/include cleaned modules, helpers, and executable fixtures
under normal strict Pyrefly. Marker-only edits require no legacy typing
migration. No production changes, reduced coverage thresholds, or CI-skipping
filter.

## Timing protocol

After marker delivery, freeze baseline revision and prepared offline
environment. Before cleanup run one untimed warm-up per selection, then three
repetitions each of full Make and unmarked selections through
`make test ARGS=test/make/integration`, setting `UV_OFFLINE=true`,
`UV_NO_SYNC=true`, and `PYTEST_ADDOPTS='--durations=0'`; the unmarked selection
adds `-m "not real_tool"`. Alternate full/unmarked runs. Repeat on final
revision with one untimed warm-up per selection before its three-run batch,
using the same host, tools, preparation, selection, and warm-cache conditions.
Record revisions, versions, commands, elapsed seconds, per-test durations,
failures, skips, medians, and deviations in `measurements.md` in this parent
directory; retain raw captured run outputs in its sibling `measurements/`
directory. Create these artifacts only after marker merge and before cleanup.
Keep failed or interrupted observations; rerun only after resolving/reporting
cause and retain both observations. Missing three successful matched runs makes
timing inconclusive. Coverage preservation is required; compare medians
separately, report slower or unchanged results honestly, and claim no unmeasured
speedup. No timing assertions or benchmark tool. Follow
[evaluation](../../../evaluation.md).

The original baseline used Python 3.14.6; inventory found that interpreter and
3.14.7. The matched refresh used old code
`96ef5bae2a322c3d1c5a530b88687e128742332c` and the stopped final attempt used
`72b5c0617e41fe01520f03095aaaea5317dc94c0`. Those frozen inputs and artifacts
are historical records; do not resume the stopped sequence. Evaluation inputs
may use exact frozen revisions; delivery branches start from current master.

Preflight both prepared offline environments on the current host before runs:
record executable paths, Python/tool/package versions, locks and cache
preparation; verify matching selections and warm-cache conditions. Freeze those
conditions through final execution, with no tool/version changes after the
baseline. Use the protocol above, scoped `GIT_CONFIG_GLOBAL=/dev/null` and
`GIT_CONFIG_NOSYSTEM=1`, and sequential invocations without another suite
running. Measure outer elapsed time with a monotonic clock around Make
launch/exit; exclude preparation, warm-ups and artifact writing from medians,
and keep pytest durations separate. Stop/report mismatches, failures, timeouts,
interruptions or unexpected skips and retain their observations; incomplete
matching is inconclusive, never silently substituted.

Execution budget is exactly eight Make invocations per condition: two warm-ups
and six measured runs, each with a 180-second timeout, identical for both
conditions. Stop on timeout or budget exhaustion and retain partial output;
no automatic extra runs. Preparation remains excluded from timing.

Preserve `measurements.md` and `measurements/` untouched. Add the separate
report `matched-measurements.md` and raw outputs/metadata in
`matched-measurements/baseline/` then `matched-measurements/final/`. Include UTC
boundaries, commands, exits, counts, skips, medians and deviations. Compare full
and unmarked medians separately: lower/equal/higher means
faster/unchanged/slower for that measured workload; no causal or general speedup
claim follows. Independent parent preservation review reuses child evidence, a
complete Make suite and latest-head full CI before acceptance; timing cannot
excuse lost coverage.

### Renewed attempt

This retained protocol governed the stopped renewed attempt. It does not
authorize resuming that sequence or another run.

After scratch isolation merges, record its exact merged SHA before preparation
or execution and create a separate corrected-final input. Reuse the retained
matched baseline only after preflight against its metadata: common host,
executable/tool/Python/package versions, lock, selectors and cache preparation.
Record new input preparation and cache conditions and their comparison limits;
stop on mismatch rather than silently refreshing baseline or replacing tools.

Reuse the shared command, isolation, timing and stop protocol above with a new
budget of exactly eight corrected-final invocations: two warm-ups then three
alternating full/unmarked pairs, 180 seconds each. No concurrent suite or extra
runs. Append the comparison to `matched-measurements.md`; retain new raw output,
metadata and driver in `matched-measurements/corrected-final/`. Preserve
original, refreshed baseline and stopped-attempt evidence bytes, including
encoded output. Report counts/workload differences and preservation limits;
unsuccessful or unmatched observations are inconclusive. Parent integration
review reuses both children, complete Make-suite execution and latest-head full
CI.

### Witness-final attempt

This retained protocol governed the
[delivered observations](matched-measurements.md#witness-final-observations-and-comparison)
and does not authorize additional runs.

After the witness correction merges, the Evaluation freezes that exact merged
revision in a separate input. Reuse the shared
command, order, timing boundaries and stop handling with a new eight-invocation
budget and 180-second timeout per invocation. Earlier protocols and all three
frozen inputs remain historical evidence, not sequences to resume.

Preflight against the retained matched baseline before execution. Fixture-owned
Git PATH narrowing is an intentional code change: baseline cleanup inherited
top-level Git 2.55.0; cleaned fixtures resolve Apple Git 2.50.1. Disclose this
confound; unrelated host/tool/Python/package/lock/selector drift stops
execution. Use the stopped corrected attempt's preparation method: copy the
preserved baseline post-batch cache to the new input, then offline Make
setup/verification. Record new cache/preparation conditions and limits; this is
not the original initial seed. No silent rebaseline, tool replacement or
automatic extra runs. Append observations to `matched-measurements.md` and
retain new raw outputs, metadata and driver in
`matched-measurements/witness-final/`, preserving all earlier evidence bytes.
Report selection medians separately or an explicit inconclusive outcome, counts
and workload/preservation limits; no causal/general speedup attribution. Parent
acceptance reuses correction evidence, complete Make-suite outcomes and
latest-head full CI.

## Acceptance

- **AC-1 TODO** Given all deliveries, retained tests prove existing routing and
  real repository effects in disposable environments; normal CI runs all cases.

  Validation: review child criterion execution, preserved coverage, strict
  inclusion, and latest-head full CI; run the complete Make suite.
- **AC-2 TODO** Given matched baseline/final runs, the timing comparison reports
  both selection medians and evidence gaps without trading coverage for speed.

  Validation: independently review protocol compliance, observations, and
  limits.
