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
- **TODO** [Final measurements and comparison](final-measurements/README.md).

Cleanup deliveries are complete;
[original baseline measurements](measurements.md) remain historical evidence.
Matched baseline is delivered; final measurements follow. Each complete leaf
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

The original baseline used Python 3.14.6; the current prepared environment
reports 3.14.7. Inventory available interpreters before execution; this does not
establish that 3.14.6 is unavailable. Refresh old baseline code at
`96ef5bae2a322c3d1c5a530b88687e128742332c` against final code frozen at
`72b5c0617e41fe01520f03095aaaea5317dc94c0`. A separate disposable checkout of
that exact old revision is authorized only as evaluation input; delivery
branches still start from current master. Later plan/report revisions are
documentation-only.

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

## Acceptance

- **AC-1 TODO** Given all deliveries, retained tests prove existing routing and
  real repository effects in disposable environments; normal CI runs all cases.

  Validation: review child criterion execution, preserved coverage, strict
  inclusion, and latest-head full CI; run the complete Make suite.
- **AC-2 TODO** Given matched baseline/final runs, the timing comparison reports
  both selection medians and evidence gaps without trading coverage for speed.

  Validation: independently review protocol compliance, observations, and
  limits.
