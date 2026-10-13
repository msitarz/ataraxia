# Executor communication Investigation

Can the orchestrator hand off a bounded task to a restricted executor, receive
its artifact or blocker, and send corrections to the same session without
granting access to the source repository?

Follow this Work's [execution gate](#execution-gate-and-limits). Findings inform
[native execution](../execution/README.md) and
[accepted import](../artifact-import/README.md); this Investigation does not
implement those commands.
Compare `codex exec` with explicit session resumption against an app-server
controller where live steering or cancellation needs it. Use current
[non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode)
and [app-server documentation](https://learn.chatgpt.com/docs/app-server), but
distinguish documented features from observed installed-client behavior.

## Trials and decision basis

Predeclare a tiny disposable task and one consolidated correction observable
in the clone. Test initial handoff, final artifact, same-session correction,
and a blocker or failed process. Declare run and correction budgets before
execution under this Work's gate; use the existing leaf model policy without
a model comparison.

Attempt the integrated restricted-session trials only when the isolation Work
establishes a usable boundary. If it cannot, retain that failure evidence and
test communication mechanics independently without claiming enforced isolation;
an evidence-based negative recommendation can complete this Investigation.

For exec, exercise stdin delivery, JSONL events, final-message capture, process
exit handling, and saving the explicit session ID. Resume that ID with the same
clone and verified restricted configuration; avoid `--last` with concurrent
sessions and `--ephemeral` when resumption is required. Confirm retained task
context without exposing other session history to executor-generated commands.
Correlate report, clone, base, and final revision to detect stale artifacts.

Use a two-session control to verify correction routing. Exercise missing output,
a failed or denied operation, and unavailable-session recovery. Distinguish a
successful process exit from verified acceptance; return blockers and partial
artifacts without false completion. Identify how the orchestrator stops a stuck
process and preserves recovery evidence.

Assess whether completion followed by resume meets
[current review rules](../../../orchestrator.md). If live control is
required, exercise app-server thread start, events, follow-up turns, steering,
and interruption under the same boundary; otherwise label that alternative
documentation-only and explain why a controller is unnecessary. No production
controller or general messaging framework belongs in this Work.

## Acceptance

- **AC-1 TODO** Actual handoff and correction attempts record whether the same
  session retains context and returns attributed commits, reports, and events.
  Where a usable isolation boundary exists, verify it before both turns;
  otherwise disclose the dependency failure and limits of independent probes.
  Validation: inspect transcripts and revisions or the established blocker;
  rerun
  [source-denial probes](../../reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/sandbox-isolation/README.md)
  when a usable restricted path exists.
- **AC-2 TODO** Routing and failure cases return a recoverable artifact or
  explicit blocker without silent fallback, cross-session correction,
  unapproved permissions, or false completion.
  Validation: inspect the routing control, failed-operation, missing-output,
  and unavailable-session cases against the declared protocol.
- **AC-3 TODO** The recommendation selects exec/resume, app-server control,
  or further investigation, with observed versus documentation-only evidence
  and required preparation and recovery effort.
  Validation: compare the candidates against actual communication needs,
  review gates, and any untested live-control claims.

Return the demonstrated handoff and correction path for
[Artifact delivery](../../reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/artifact-delivery/README.md).
Preserve evidence and promote lasting findings under the normal Investigation
lifecycle.

## Execution gate and limits

The [preserved preparation input](../preparation-input.md) supports only the
tested Darwin Intel deterministic condition; no model session or filtered-answer
condition was established. Merge the reviewed ownership correction before Work
execution. Before any model-backed trial, declare frozen fixtures and revisions,
prompts, conditions, permitted resources, selected model and effort, maximum
runs and corrections, a time or token budget and stop handling; obtain
applicable maintainer approval. Use the existing leaf policy without a model
comparison. This plan authorizes no runs.

Use disposable repositories and non-secret canaries. Verify the intended
source/history, command-network and other-session exclusions before initial and
resumed restricted trials; preparation alone proves no session isolation.
A failed boundary blocks integrated trials without broader-access rescue;
preserve failures, partial artifacts, timing and deviations. Independent
communication probes require declared conditions and applicable authorization
and cannot claim enforced isolation. Retain existing review, evidence-before-
cleanup, signing and publication gates. New sandbox systems, production tooling,
comparative performance and live GitHub publication trials need separate scope
and applicable authorization; this relocation adopts no default policy.
