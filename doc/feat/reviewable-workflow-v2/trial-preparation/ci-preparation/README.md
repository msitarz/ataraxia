# CI preparation

Measure and reduce preparation that CI jobs perform without using it.

The CI check, test, and example targets use [ci-setup](../../../../../Makefile)
to synchronize locked development dependencies. The check and full CI targets
prepare hook environments. The package target runs its isolated wheel smoke
check directly, which builds its own wheel.

With CI scheduling delivered in the [trial-preparation map](../README.md),
record a baseline before changing preparation, separating cold and warm
caches and stating the environment, commands, repetitions, and variability.
Allocate dependency, hook, and build preparation to their actual consumers.
Define the success threshold from that baseline before accepting the
optimization, and report the result or an evidence-based decision to retain
the existing setup.

## Measurement and outcome

Baseline `make ci-setup` on macOS with CPython 3.14.6, uv from `pyproject.toml`,
an empty project environment, and a new isolated uv cache took 7.937 seconds.
It fetched and installed the 40 locked development packages, prepared hooks,
and built the wheel. A warm run with the same environment and cache took
0.245 seconds. Three additional warm baseline runs using the same pre-change
Makefile took 0.238–0.246 seconds (median 0.244 seconds).

Before accepting the change, the success threshold was at least a 25% reduction
in warm shared CI setup time, no cold setup regression greater than 10%, and no
development hook/build, installed-package, lock, offline, or full-audit gate
regression. The changed cold `make ci-setup` took 1.418 seconds with a new
project environment and empty uv cache; it fetched and installed the same 40
locked packages. Three warm runs took 0.062–0.081 seconds (median 0.066
seconds), a 73% reduction from the warm baseline. Cold runs were single
observations with independent network fetches, so the apparent cold reduction
is not treated as a precise estimate of hook/build cost. The package target
skips shared dev setup and its real wheel smoke check passed in 1.654 seconds
with a fresh empty environment and cache. The smoke test still built and
installed the wheel and checked CLI output and result JSON.

The shared CI preparation now locks and syncs development dependencies only;
the check job prepares its hook environments, while the package job runs the
installed-wheel check without a development sync. `make setup` retains hook
installation, hook preparation, and wheel build tooling for later offline
verification. Dependency sync still uses `--locked`, `make verify-setup` still
checks rather than repairs a missing or stale environment, offline targets
remain offline, and full CI still runs the vulnerability audit after local
checks. Focused Make orchestration tests passed (29 tests); `make ci-check`
passed its offline checks and vulnerability audit, and `make verify-setup`
accepted the prepared environment. The missing-environment probe failed
clearly with “The environment is outdated; run `uv sync` to update the
environment.” Full `make ci` was not run locally.

## Acceptance

- **AC-1 DONE** The delivery PR reports a representative baseline, the proposed
  preparation change, a declared success threshold, and comparable results;
  any decision to retain existing behavior explains the measured tradeoff.
  Verification: this Work records cold and warm setup times, cache/network
  conditions, repetitions, variability, and the declared threshold above.
- **AC-2 DONE** Each CI target prepares what its checks require, and missing
  required environments fail clearly. `make setup` still prepares hooks and
  build tooling for subsequent offline verification.
  Verification: focused Make regression tests check the target recipes and
  `make ci-package` exercised the installed wheel without shared dev setup.
- **AC-3 DONE** Prepared offline verification remains network-free, rejects a
  missing or stale environment, and exercises the installed package outside
  the checkout. Dependency synchronization stays locked and audit remains
  required by full CI.
  Verification: the locked sync completed from a fresh isolated environment;
  package smoke check passed. Offline and full-audit recipes and their gates
  were preserved; full `make ci` was not run locally.

Use focused Make orchestration regression tests and real setup or verification
evidence for the affected paths. Follow
[validation policy](../../../../validation.md) when distinguishing local,
offline, network, and CI results. If measurements support retaining the current
recipes, verify these compatibility criteria against those recipes.
