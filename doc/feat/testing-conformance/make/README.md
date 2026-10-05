# Make testing boundaries

Preserve Make contracts with fast real-Make/fake-uv orchestration and selected
real-tool regressions. Follow [testing](../../../testing.md),
[integration guidance](../../../testing-integration.md), and
[test ownership](../../../test-ownership.md).

## Delivery map

- **TODO** [Real-tool selection](real-tool-selection/README.md).
- **TODO** [Stub environment](stub-environment/README.md).
- **TODO** [Check orchestration](check-orchestration/README.md).
- **TODO** [Worktree creation](worktree-creation/README.md).
- **TODO** [Worktree cleanup](worktree-cleanup/README.md).
- **TODO** [Documentation boundary](documentation-boundary/README.md).
- **TODO** [Acceptance targets](acceptance-targets/README.md).
- **TODO** [Size guardrails](size-guardrails/README.md).

Merge this map before child delivery. Marker delivery and baseline measurement
precede all cleanup. Stub helper precedes routing, orchestration, and creation.
Sequence parent-map, helper, and Pyrefly inclusion edits. Extract
responsibilities from the large `test_makefile.py` into focused modules rather
than annotating its unrelated legacy tests. Stub environment is split because
helper introduction plus all routing migration exceeds one review question. Each
complete leaf diff must fit the
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

## Acceptance

- **AC-1 TODO** Given all deliveries, retained tests prove existing routing and
  real repository effects in disposable environments; normal CI runs all cases.

  Validation: review child criterion execution, preserved coverage, strict
  inclusion, and latest-head full CI; run the complete Make suite.
- **AC-2 TODO** Given matched baseline/final runs, the timing comparison reports
  both selection medians and evidence gaps without trading coverage for speed.

  Validation: independently review protocol compliance, observations, and
  limits.
