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

Actual attempts on a predeclared tiny disposable task and one consolidated
correction record whether the same session retains context and returns
attributed commits, reports and events. Exec observations cover stdin delivery,
JSONL events, final-message capture, process exit handling and saving an
explicit session ID. Resume uses that ID, the same clone and verified restricted
configuration, without `--last` in concurrent sessions or `--ephemeral` when
resumption is needed. Report, clone, base and final revision correlate to expose
stale artifacts; retained task context does not expose other session history to
child commands.

A usable boundary is established before both integrated restricted turns. If
enforcement cannot supply one, retained failure evidence and separately
authorized independent communication probes disclose the limit rather than claim
enforced isolation. Transcripts and clone revisions or an established blocker
support the finding; a negative recommendation can complete this Investigation.

### **AC-2 TODO** Return recoverable routing and failure outcomes

A two-session control establishes correction routing. Missing output, a failed
or denied operation and unavailable-session recovery return attributed partial
artifacts or an explicit blocker without silent fallback, cross-session
correction, unapproved permissions or false completion. Successful process exit
remains distinct from verified acceptance. The demonstrated path identifies how
the orchestrator stops a stuck process and preserves its recovery evidence.

### **AC-3 TODO** Recommend the fitting communication path

The recommendation selects exec/resume, app-server control or further
investigation against actual communication needs and
[current review rules](../../../orchestrator.md). It compares checked fit,
required preparation/recovery effort and remaining uncertainty using primary
[non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode)
and [app-server documentation](https://learn.chatgpt.com/docs/app-server),
separating documented features from observed installed-client behavior.

If live control is required, observations cover app-server thread start, events,
follow-up turns, steering and interruption under the same boundary. Otherwise
that alternative remains documentation-only with the reason a controller is
unnecessary; untested live-control claims stay explicit. No production
controller or general messaging framework is delivered. The demonstrated
handoff/correction path informs [native execution](../execution/README.md) and
[accepted import](../artifact-import/README.md) without implementing their
commands; lasting findings follow the
[Investigation lifecycle](../../../work-definition.md#investigations).

## Dependencies

- **TODO** [Enforced runtime readiness](../enforcement/README.md): supplies a
  usable boundary before integrated restricted trials, with the failure path
  and separate authorization limits defined by AC-1 and the execution gate.

## Execution gate and limits

The [preparation input](../preparation-input.md) supports only its tested Darwin
Intel deterministic condition. The separate
[isolation input](../isolation-input.md) records a tiny standalone model/session
result under its own frozen condition; it establishes no full-project model
session or filtered current-tree answer exclusion. Neither input completes
enforcement readiness for this Work. Merge the reviewed ownership correction
before Work execution. Before any model-backed trial, declare frozen fixtures
and revisions, prompts, conditions, permitted resources, selected model and
effort, maximum runs and corrections, a time or token budget and stop handling;
obtain applicable maintainer approval. Use the existing leaf policy without a
model comparison. This plan authorizes no runs.

Use disposable repositories and non-secret canaries. Verify the intended
source/history, command-network and other-session exclusions before initial and
resumed restricted trials; preparation alone proves no session isolation.
A failed boundary blocks integrated trials without broader-access rescue;
preserve failures, partial artifacts, timing and deviations. Independent
communication probes require declared conditions and applicable authorization
and cannot claim enforced isolation. Retain existing review, evidence-before-
cleanup, signing and publication gates. New sandbox systems, production tooling,
comparative performance and live GitHub publication trials need separate scope
and applicable authorization; this Investigation adopts no default policy.
