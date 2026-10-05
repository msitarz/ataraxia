# Current dependency snapshot compatibility

Add Make-owned CI integration that exercises the implemented snapshot pipeline
against the checked-out PR's declared dependency versions. Run it through the
ordinary
[pull-request CI workflow](../../../../../../../../../../.github/workflows/ci.yml)
for all PRs, including dependency updates, without Dependabot-specific routing.
Own recurring cache-format and offline-install compatibility; the
[parent](../README.md) owns composition and its initial offline validation. This
is a plan, not an observed compatibility result.

Execution requires the parent's completed composition utility and the reviewed
[pinned hook selector](../../pinned-hook-sources/README.md). It also requires a
registry-selector follow-up, not yet defined as a Work, that removes duplicated
tool-version literals and reads canonical pins from pyproject.toml/uv.lock.
Define and review that follow-up before starting this child; do not add a
parallel pin catalogue here. Current tool pins must remain distinct from the
adapter's explicit supported platform, index and cache-layout validation. A
current version alone must never authorize a new layout or unsupported
condition; compatibility failures require reviewed adapter support.

On a declared supported CI platform, provision the required interpreters before
the offline phase. Prepare a fresh dedicated online cache using the actual
pinned Make setup and hook contracts from the
[tested recipe](../../../../sandbox-isolation/successful-recipe.md#project-setup-through-make-with-fresh-offline-environments).
Isolate its cache roots from hosted/restored CI caches and prior environments.
Use the reviewed preparation/provenance procedure and allowed dependency
boundary for registry and hook selection, then compose/copy the frozen snapshot.
Bind observed tool/dependency versions, declaration digests, origins, selected
entries and supported condition to that snapshot's retained evidence; do not
relabel historical preparation for a newer PR.

Recreate fresh environments and pinned hooks from the composed snapshot through
actual offline Make installation and readiness contracts. Disable network access
for that phase and allow no fallback; uv offline flags alone are not evidence of
network isolation. Provisioned interpreters remain outside the dependency
snapshot, and old virtual/hook environments must not supply the result. Preserve
input caches and retain partial destinations, commands, exit statuses and
diagnostics on failure. The existing
[registry trust boundary](../../registry-selection.md) still applies; CI does
not authenticate arbitrary caches or approve new platform/index/layout support.

No model runs, sandbox adoption, executor launch, clone/import implementation or
default worktree-policy change belongs here. Keep the complete CI integration,
tests and evidence reviewable in about five minutes; split before execution if
the isolation or recurring validation needs a separately reviewable outcome.

## Acceptance

- **AC-1 TODO** Ordinary PR CI uses the PR's canonical declared dependencies to
  prepare a fresh isolated dedicated cache, select registry and pinned hook
  inputs, compose the snapshot and successfully recreate fresh offline
  installation, readiness and hooks on the declared supported condition. The
  retained snapshot evidence identifies the exact observed inputs, and existing
  cache/environment state cannot supply preparation or offline success.

  Validation: Criterion-marked deterministic tests exercise canonical input
  selection, cache isolation and ordered Make integration. Retain an actual
  latest-head CI run of online preparation through composed selection/copy and
  network-disabled fresh offline Make setup/readiness/hook recreation.
  Independently review the declaration/version/origin trace, resolver
  completeness, supported-condition checks and phase isolation against the
  tested recipe.
- **AC-2 TODO** A missing selected artifact or stale/incompatible condition
  fails the recurring CI check with inspectable diagnostics and retained
  evidence/destinations, without cache mutation, overwrite, silent online
  fallback or automatic acceptance of a newly current tool layout.

  Validation: Criterion-marked tests cover missing artifacts, stale declarations
  and unsupported conditions. Retain actual negative CI checks for a missing
  offline artifact and a stale condition, including command exits and preserved
  failure artifacts. Independently review the recovery guidance and verify that
  the offline failures could not fetch replacements.
