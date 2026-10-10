# 19. Delegate mechanical PR publication

Date: 2026-10-10

## Status

Accepted

Amends
[17. Review local artifacts before PR publication](0017-review-local-artifacts-before-pr-publication.md).

## Context

WDR 17 assigns local review and publication to the owning orchestrator. The
[publisher Work](https://github.com/msitarz/ataraxia/blob/c10397f40b5a251b0511260c201e9a17a46f4db4/doc/feat/publication-tool-guidance/publisher/README.md)
separates mechanical push/create/update from that agent's judgment and
accountability. Direct orchestrator execution avoids a handoff; delegation adds
an input check and report while isolating mechanical operations. No cost savings
are measured.

## Decision

Permit a distinct reusable publisher operational subagent, using the explicitly
authorized Luna at medium effort, to publish exact reviewed inputs under
[publisher guidance](../publisher.md). The orchestrator
retains independent artifact and description review, acceptance and final-CI
assessment, publication accountability, and maintainer handoff. The publisher
stops on input mismatch, divergence, refusal, or uncertainty and cannot change
content, review, merge, comment, or bypass gates.

Only mechanical execution changes. WDR 17's local review and ready-PR sequence,
WDR 21's local acceptance before publication, maintainer authority, final-head
full CI, and general leaf-executor policy remain in force.

## Consequences

The handoff must identify exact approved inputs and rewrites must retain the
explicit expected-remote lease. Publication observations remain distinct from
acceptance and CI assessment. Delegation establishes no speed or cost advantage.
