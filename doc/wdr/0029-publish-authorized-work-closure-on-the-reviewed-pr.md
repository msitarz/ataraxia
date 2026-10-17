# 29. Publish authorized Work closure on the reviewed PR

Date: 2026-10-17

## Status

Accepted

Amends
[2. Let parent maps track Work lifecycle](0002-let-parent-maps-track-work-lifecycle.md)
for incomplete closure,
[18. Delegate verified post-merge cleanup to cleaner](0018-delegate-verified-post-merge-cleanup-to-cleaner.md)
for future command ownership after delivery, and
[28. Retain Work contracts until authorized closure](0028-retain-work-contracts-until-authorized-closure.md)
for abort and publication boundaries, and
[9. Require verified evidence for Work completion](0009-require-verified-work-completion.md)
for preserving criterion identities and dispositions when incomplete Works
close as aborted. Their other requirements remain in force.

## Context

Closure authorization belongs to the maintainer's session instruction, while
mechanical publication and Git cleanup need distinct operational boundaries.
The existing criterion checker does not accept `ABORT`, so incomplete closure
cannot safely be recorded until that support is delivered. Existing guidance
also assigns post-merge cleanup to the cleaner role.

## Decision

The maintainer's spoken or written instruction in the session is the sole
authorization to close selected Works; no token, file, extra ceremony, or tool
proof of chat authorization is required. Session context may establish that a
response such as “its ok” authorizes the closure in question. Generic
implementation acceptance does not.

When selected criteria remain `TODO`, the planned
`make work-close ARGS='path/to/README.md'` reports them and pauses without
changes so the agent can relay the question. Only after explicit confirmation by
the maintainer may it be rerun with `ABORT_REMAINING=true`, a semantic choice
rather than an authorization token. Confirmation records remaining criteria and
the Work as `ABORT` with a reason; completed Works close as `DONE`. Until the
checker supports `ABORT`, an incomplete closure request pauses without writing
unsupported headings. Completed Works may use the existing Executor,
Orchestrator, and Publisher roles for authorized mechanical closure. Criterion
identities and abort dispositions must remain inspectable in committed Git
history after contract deletion; the command Work chooses how to preserve that
history.

Closure commits use the same reviewed open PR branch, ordinary push, and
existing hooks and signing. Clean state, exact reviewed and remote tips,
authorized selection, and unambiguous reference updates are required. Refusal
or failure preserves recoverable state; there is no force push, protection
bypass, direct-master publication, or separate closure PR. Full CI on the final
closure head and maintainer merge remain required. Post-merge cleanup remains
separate and requires verified merged closure provenance; current guidance
continues to assign it to the cleaner until the command Work delivers that
responsibility. Its planned thin interface is
`make work-cleanup PR=<number>`.

## Consequences

Maintainer control is explicit without asking tooling to authenticate chat.
Incomplete closure remains unavailable until checker support exists. The future
Make interfaces are planned, not executable features of this decision. Current
closure rules live in
[Work acceptance](../acceptance-tracing.md#authorized-closure), and current
cleanup practice remains usable while command ownership is pending. See the
[lifecycle Work](https://github.com/msitarz/ataraxia/blob/e4627be3eaadb2a62ec85c8cf6cc740db026fe33/doc/feat/post-merge-work-closure/lifecycle/README.md)
and the [command Work](../feat/post-merge-work-closure/command/README.md) for
planned tool delivery. This decision does not close any Work.
