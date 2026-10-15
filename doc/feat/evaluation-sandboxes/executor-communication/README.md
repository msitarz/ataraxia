# Executor communication Investigation

## Purpose

Determine how an orchestrator can hand off a restricted task, receive its
artifact or blocker and correct the same session without exposing the source
repository.

## Goals

- Compare native exec/resume with app-server control for actual communication
  needs.
- Establish attributable same-session correction and recoverable failure
  routing.
- Recommend a demonstrated path or further investigation with explicit limits.

## Mechanisms

- `codex exec` and explicit session resume provide the native candidate for
  non-interactive handoff, events and follow-up turns.
- The Codex app-server provides the alternative candidate when live steering
  or cancellation requires a controller.

## Acceptance criteria

### **AC-1 TODO** Establish attributed handoff and same-session correction

Handoff and correction findings show whether one session retains context and
returns attributable work.

- A predeclared tiny disposable task and one consolidated correction produce
  attributed commits, reports and events, or an established blocker with
  transcripts/revisions.
- Exec observations cover stdin delivery, JSONL events, final-message capture,
  process exit and explicit session ID retention.
- Resume uses that ID, the same clone and verified restricted configuration
  without concurrent-session `--last` or resumption-incompatible `--ephemeral`.
- Report, clone, base and final revision correlate to expose stale artifacts
  without exposing other session history to child commands.
- A usable boundary precedes both restricted turns, or retained enforcement
  failure and separately authorized independent probes disclose their lack of
  enforced isolation.

An evidence-based negative recommendation can complete this Investigation.

### **AC-2 TODO** Return recoverable routing and failure outcomes

Routing and failure cases return attributable partial artifacts or explicit
recoverable blockers.

- A two-session control establishes correction routing.
- Missing output, failed/denied operations and unavailable-session recovery
  permit no silent fallback, cross-session correction, unapproved permissions or
  false completion.
- Successful process exit remains distinct from verified acceptance.
- The demonstrated path identifies how to stop a stuck process and preserve
  recovery evidence.

### **AC-3 TODO** Recommend the fitting communication path

The recommendation selects exec/resume, app-server control or further
investigation against actual needs and [review rules](../../../orchestrator.md).

- Candidate comparisons record checked fit, preparation/recovery effort and
  uncertainty against primary
  [non-interactive](https://learn.chatgpt.com/docs/non-interactive-mode) and
  [app-server](https://learn.chatgpt.com/docs/app-server) references,
  distinguishing documentation from installed-client observations.
- Required live control is observed through app-server thread start, events,
  follow-up turns, steering and interruption under the same boundary.
- Otherwise app-server remains documentation-only with the reason a controller
  is unnecessary, and untested live-control claims stay explicit.
- Findings inform [native execution](../execution/README.md) and
  [accepted import](../artifact-import/README.md) without delivering their
  commands, a production controller or a messaging framework.

Lasting findings follow the
[Investigation lifecycle](../../../work-definition.md#investigations).

## Dependencies

- **TODO** [Enforced runtime readiness](../enforcement/README.md): supplies a
  usable boundary before integrated restricted trials, with the failure path
  and separate authorization limits defined by AC-1 and the execution gate.

## Execution gate and limits

Trials require frozen conditions and applicable maintainer approval; this
contract authorizes no runs.

- [Preparation input](../preparation-input.md) supports only its Darwin Intel
  deterministic condition, and [isolation input](../isolation-input.md) only its
  frozen tiny standalone model/session result, establishing neither a
  full-project model session, filtered current-tree answer exclusion nor current
  readiness.
- The reviewed ownership correction must merge before Work execution.
- Model-backed trials predeclare fixtures/revisions, prompts, conditions,
  permitted resources, model/effort, maximum runs/corrections, time or token
  budget and stop handling under the existing leaf policy without model
  comparison.
- Disposable repositories and non-secret canaries establish source/history,
  command-network and other-session exclusions before initial/resumed restricted
  turns, without inferring isolation from preparation.
- Failed boundaries block integrated trials without broader-access rescue,
  retaining failures, partial artifacts, timing and deviations.
- Independent probes need declared conditions and applicable authorization and
  cannot claim enforced isolation.
- Existing review, evidence-before-cleanup, signing and publication gates remain
  required.
- New sandbox systems, production tooling, comparative performance and live
  GitHub publication trials require separate scope/authorization, and no default
  policy is adopted.
