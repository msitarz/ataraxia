# 7. Require CI on the reviewed head

Date: 2026-10-01

## Status

Proposed

## Context

Running full local CI before every draft PR can catch integration issues early,
but repeats PR checks and depends on access to the network audit. It delays
review of small changes even though the full CI workflow evaluates the pushed
PR revision.

## Decision

Run checks affected by a change while preparing a draft; a full local `make ci`
run is optional. Require the full CI workflow to pass on the latest reviewed PR
head before merge. Local checks and offline verification do not replace that
gate.

## Consequences

Review can begin with focused evidence, while failures in broader checks may
surface later. Keep the CI workflow and offline verification limitations in
their owners: [validation policy](../validation.md) and
[CI workflow](../../.github/workflows/ci.yml). See
[PR 89](https://github.com/msitarz/ataraxia/pull/89).
