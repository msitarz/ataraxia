# CI preparation

Measure and reduce preparation that CI jobs perform without using it.

Every CI entry point depends on [ci-setup](../../../../../Makefile), which
synchronizes development dependencies, prepares all hook environments, and
builds a wheel. Test and example jobs do not invoke hooks or package checks;
the package smoke check builds its own wheel.

Deliver [CI scheduling](../ci-scheduling/README.md) first. Record a baseline
before changing preparation, separating cold and warm caches and stating the
environment, commands, repetitions, and variability. Allocate dependency,
hook, and build preparation to their actual consumers. Define the success
threshold from that baseline before accepting the optimization, and report the
result or an evidence-based decision to retain the existing setup.

## Acceptance

- **AC-1 TODO** The delivery PR reports a representative baseline, the proposed
  preparation change, a declared success threshold, and comparable results;
  any decision to retain existing behavior explains the measured tradeoff.
  Verification: review measurements for cold and warm preparation, including
  network and cache conditions, against the declared threshold.
- **AC-2 TODO** Each CI target prepares what its checks require, and missing
  required environments fail clearly. `make setup` still prepares hooks and
  build tooling for subsequent offline verification.
- **AC-3 TODO** Prepared offline verification remains network-free, rejects a
  missing or stale environment, and exercises the installed package outside
  the checkout. Dependency synchronization stays locked and audit remains
  required by full CI.

Use focused Make orchestration regression tests and real setup or verification
evidence for the affected paths. Follow
[validation policy](../../../../validation.md) when distinguishing local,
offline, network, and CI results. If measurements support retaining the current
recipes, verify these compatibility criteria against those recipes.
