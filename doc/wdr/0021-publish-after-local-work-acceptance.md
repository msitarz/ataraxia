# 21. Publish after local Work acceptance

Date: 2026-10-09

## Status

Accepted

Amends
[15. Use CI results as evidence of mechanical checks](0015-use-ci-results-as-evidence-of-mechanical-checks.md)
and
[17. Review local artifacts before PR publication](0017-review-local-artifacts-before-pr-publication.md).

## Context

Work criteria may be verified by local behavior tests, type checks, or manual
review while full PR CI remains the required merge gate. Requiring CI before
every criterion is accepted can make the ordinary sequence circular: publishing
starts CI, but the acceptance contract requires both verification and cleanup
commits before publication. CI-specific criteria still require their actual
CI result and cannot be completed by local evidence.

## Decision

Follow the criterion's declared `Validation:` method. When that method is
locally executable, complete and independently review its evidence, preserve
verified acceptance and the separate cleanup in their required commits, then
publish the reviewed branch once. Require full CI on the latest reviewed PR head
before merge consideration. Do not mark a criterion complete when its method
explicitly requires a CI result until that result is observed; do not waive that
method to fit the ordinary sequence. Seek maintainer steering if a CI-specific
criterion cannot be satisfied without changing the sequence.

A material correction after publication remains permitted. Return affected
criteria to `TODO`, refresh evidence, obtain independent review, and require
fresh full CI on the corrected head. A planned single publication does not
prohibit necessary corrections or a later publication.

Keep criterion status, evidence, and Work commits in
[acceptance tracing](../acceptance-tracing.md). Keep PR publication in
[pull-request guidance](../pull-requests.md), and the full CI merge gate in the
[check and evidence policy](../validation.md). Preserve WDR 7's latest-head CI
gate, WDR 9's observed acceptance and separate cleanup commits, and maintainer
review and merge authority.

## Consequences

Ordinary local acceptance can be recorded before CI runs without claiming CI
success. CI remains authoritative for mechanical outcomes and mandatory before
merge. Explicit CI-dependent acceptance remains unresolved until observed, and
corrections retain a path to refreshed evidence and CI without weakening the
original gate. See the
[single-publication delivery Work](../feat/single-publication-delivery/policy/README.md).
