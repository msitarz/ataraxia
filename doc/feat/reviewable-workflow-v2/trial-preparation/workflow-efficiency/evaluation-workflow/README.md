# Evaluation workflow

Define reusable guidance for empirical evaluations before local trial methods
disappear with completed Works. The
[leaf-agent comparison PR](https://github.com/msitarz/ataraxia/pull/122) and its
[preserved evidence](https://github.com/msitarz/ataraxia/blob/d79a39c45961fd3d58519572a45ccbeae707d443/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/leaf-agent-selection/controlled-comparison/results.md)
provide motivating evidence, including indexed-answer exposure and derived
change-size measures that need explicit treatment. The PR remains a separate
Work; this plan neither assumes its merge nor adopts its findings as policy.

This Work defines Evaluation as a kind of Work that owns empirical
evidence from a declared protocol. Investigation owns a bounded recommendation;
Prototype answers feasibility through exploratory implementation. An
Investigation may use an Evaluation, while a small comparison may stay inline.
All use normal scope, lifecycle, review, evidence, and cleanup rules.

## Intended ownership and outcome

Deliver one review outcome: a discoverable, reusable Evaluation contract with
clear boundaries between empirical evidence, recommendations, and policy
adoption. Aim for the
[five-minute review target](../../../../../workflow.md#scope-and-sizing) across
the complete change; reassess the actual diff before delivery and split the plan
for review before expanding if that target cannot be met.

- `doc/workflow.md` owns Work kinds, their relationships, and common lifecycle.
- A new `doc/evaluation.md` owns independently triggered guidance for designing,
  running, and interpreting empirical evaluations.
- Each specific Work README and linked protocol owns its question, inputs,
  conditions, budget, metrics and checks, thresholds, completion, and evidence.
- A WDR owns concise decision rationale, alternatives, and tradeoffs. The
  [WDR workflow](../../../../../wdr-workflow.md) retains eligibility, and the
  [decision-record format](../../../../../decision-records.md) retains status
  and lifecycle. Choose the number at implementation time; link to those
  procedural owners rather than duplicating them.
- `doc/ubiquitous-language.md` owns the Evaluation definition and owner link;
  `doc/README.md` owns the owner inventory, and `AGENTS.md` the conditional
  reading route for empirical evaluation tasks.

Reuse [orchestration](../../../../../orchestrator.md),
[acceptance tracing](../../../../../acceptance-tracing.md), and
[checks and evidence](../../../../../validation.md) through links. The existing
[trial-contract Work](../../trial-contract/README.md) remains the specific
live-trial owner; it may link general evaluation guidance without a broad
rewrite.

## Acceptance

- **AC-1 DONE** The owner documents define Evaluation and distinguish its
  empirical evidence from Investigation recommendations and Prototype
  feasibility. Conditional reading reaches the focused evaluation owner;
  normal Work lifecycle and review apply without compulsory nesting or agents.
  Validation: inspect the glossary, Work guidance, owner inventory, and
  reading route; walk through an independent Evaluation, an Investigation using
  one, and a small inline comparison.
- **AC-2 DONE** Reusable guidance requires a predeclared question, conditions,
  common quality and preservation rubric, and decision thresholds. Protocols
  identify frozen fixtures, guidance, tools, prompts, permitted resource and
  reference access, and verified isolation where needed; they define
  repetitions, order, freshness, bounded dispatch and correction limits, and
  stop handling.

  Validation: walk through matched comparison and contamination
  examples, checking that conditions and limits are inspectable before
  execution.
- **AC-3 DONE** Guidance makes initial and final artifacts, severity findings,
  executor and parent checks and evidence reuse, timestamps and timing
  boundaries inspectable. It distinguishes preparation effort, source and test
  change sizes, test counts, and available active time, token use, and cost;
  unknown measurements stay unknown. Evidence records disclose deviations,
  contamination, confounds, reviewer identity, and blinding status. Comparisons
  match tasks rather than pooling unlike workloads, and distinguish
  observations, recommendations, and policy adoption.

  Validation: review example evidence with missing cost data, indexed-answer
  exposure, derived change sizes, and unlike tasks; confirm conclusions remain
  bounded by their declared protocol and available evidence.
- **AC-4 DONE** A concise adoption-ready WDR explains the choice and meaningful
  alternatives under the existing maintainer acceptance lifecycle. Guidance
  preserves empirical artifacts through existing Git and PR evidence procedures,
  without routine per-revision bookkeeping or a second lifecycle.
  Validation: inspect the WDR and links against the shared decision-record
  format and Work evidence procedure; walk through evidence preservation and
  distinguish plan merge, decision acceptance, and implementation completion.

## Execution gate and limits

Implement only after this plan and its parent map are reviewed and merged,
following the [Work workflow](../../../../../workflow.md) and
[WDR workflow](../../../../../wdr-workflow.md). Reconcile overlapping owner
edits against current `master`; directory ancestry does not choose the branch
base. Plan merge does not adopt policy or authorize an evaluation, model choice,
or trial. Actual execution needs its own bounded protocol and applicable
approval.

This planning delivery changes only this README and its parent TODO map. Future
implementation adds owner guidance and decision rationale; it does not run
trials, select a winning model, or generalize a particular 18-run budget, model
set, or cutoff into global policy. Do not add mandatory templates, journals,
schemas, agents, or lifecycle machinery. Preserve existing live-trial ownership
and maintainer review, merge, and CI gates.
