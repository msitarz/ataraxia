# Empirical evaluations

Read when designing, running, or interpreting an empirical evaluation, whether
it is an independent Evaluation Work, supports an Investigation, or is a small
comparison kept inline. [Work definition](work-definition.md#evaluations) owns
Evaluation contract requirements; [Work workflow](workflow.md) owns lifecycle; a
specific Work README and linked protocol own the experiment.

## Declare the protocol before execution

State the bounded question, conditions, budget, common quality and preservation
rubric, metrics and checks, decision thresholds, and completion conditions.
Define severity levels and how failed quality or preservation checks affect the
comparison. Declare thresholds for success, reconsideration, and inconclusive
results before seeing outcomes; do not select a winner from timing alone.

Identify frozen fixtures and revisions, guidance, tools and versions, prompts,
and permitted resource and reference access for each condition. Match tasks
across conditions; state intended differences and hold other inputs constant
where possible. Verify required isolation rather than assuming a Worktree is a
security boundary. Check reachable history, indexes, reference answers, caches,
and prior session context for unintended exposure.

Define repetitions, execution order, freshness of sessions and inputs, bounded
dispatch and correction limits, and stop handling. Specify how timeouts,
failures, interrupted runs, exhausted budgets, and contaminated runs are
retained, excluded, or rerun. Record deviations rather than silently replacing
failed observations. Use [orchestrator guidance](orchestrator.md) when
delegating; an evaluation itself does not require agents or nesting.

## Prepared-clone boundary and handoff

Read this section when preparing an independent evaluated fixture with the
[native contribution procedure](../CONTRIBUTING.md#preparing-an-evaluated-fixture-clone).
Use the existing Work/protocol and execution records, without a new template or
lifecycle. Before any future authorized manual check, freeze the selected
commit, lock/hook declarations, final paths, tools/platform, resolved
interpreter and hook runtimes, intended boundary, permitted files/references and
scratch, plus commands and failure handling. Historical examples are not current
readiness.

Before the first Git/clone operation, review and sanitize effective Git, uv,
prek, Python and shell configuration: remove inherited object/cache/environment
paths, includes, source hooks and credential-bearing settings; declare required
tool/runtime reads and clone-local caches explicitly. Inspect editable links,
interpreter and hook launch paths and readable dependency content for
source/history, reference answers, credentials and unintended external roots.
Keep reviewer records, controls and excluded answers outside executor access. If
prohibited answers or prior evidence occur in the selected committed tree or
indexes, stop for a reviewed fixture decision; shallow history removal cannot
exclude current-tree content. Do not silently filter the frozen input. Record
relevant effective configuration without retaining secrets or host auth records;
an uncaptured effective environment remains an evidence limit.

Before handoff, test useful prepared tools and installed pre-commit/commit-msg
hooks under the actual intended native restricted boundary using clone-local
scratch and the frozen configuration, without installation or synchronization.
Use matching unrestricted non-secret controls and actual denied source-file/Git,
old-object/local-fetch, source-symlink and command-network probes. An absent
origin, offline flags or a shallow object set cannot establish isolation.
Unsupported enforcement, failed/invalid controls, exposure, missing tools or
hooks, installation attempts and timeouts block handoff. Preserve commands,
statuses, outputs, denials and deviations; retain recoverable partial state
without silent retry or wider-access fallback. Further execution needs the
protocol's approval.

The existing handoff records bind the exact input and executor branch to
accepted setup/privacy inspection and restricted readiness evidence, permitted
reads and scratch, exclusions and unresolved limits. Runtime must independently
recheck its effective boundary before actual start or exact-session resume; this
preparation gate neither implements a launcher nor establishes model/session
isolation. Accepted-output review/import into the full-history Work branch
retains its own gates. Production commits preserve existing signing settings;
do not disable signing or change host settings. Any hermetic fixture identity
is distinct and belongs to the runtime/protocol.

The
[verified native-preparation report](https://github.com/msitarz/ataraxia/blob/c9a24b3f8cccfb9392ec12db2029dfe03887786d/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/environment-preparation/README.md)
and its linked evidence support only their original frozen `d8b3dd7…` input on
Darwin 25.6 x86_64 with Codex 0.162.1, Git 2.56.0, GNU Make 4.4.1, uv 0.13.0 and
Python 3.15.0 (hooks also used Python 3.14). They record fresh setup, restricted
deterministic tools/hooks and matched denial controls, including retained failed
controls and launcher deviations. The full effective environment was not
captured; current-tree audit content was permitted. They establish no
filtered-answer exclusion, model-session start/resume, other-platform support,
setup-failure recovery or artifact-import proof. Reuse their bounded evidence,
not historical cache inventories; a future condition needs its own frozen checks
and actual privacy controls. No new trial is authorized by this guidance.

## Retain inspectable observations

Keep initial and final artifacts, severity findings, executor checks, parent
checks, and the provenance of reused evidence. Identify artifact revisions and
which checks apply to each. Apply [checks and evidence](validation.md) and
[acceptance tracing](acceptance-tracing.md#planned-validation-and-evidence);
planned checks and reported assertions do not establish observed outcomes.

Record timestamps and timing boundaries, including preparation, dispatch,
executor start, completed artifact, and review or PR readiness where relevant.
Distinguish elapsed time from available active time and separate preparation,
execution, correction, reporting, and review effort. State units and measurement
methods for source and test change sizes, derived sizes, and test counts; they
are different measures, not interchangeable estimates of quality or effort.
Record token use and cost when available. Leave unknown measurements unknown,
rather than estimating them from elapsed time or change size.

Disclose deviations, contamination, confounds, reviewer identity, and whether
review was blinded. For example, indexed access to a reference answer is
exposure even without a reported file read; preserve the affected observation
and limit its interpretation according to the declared stop handling. A derived
change-size measure must identify its source artifacts and calculation. Missing
cost data permits a bounded timing or quality conclusion, not a cost claim.

## Interpret and preserve evidence

Compare matched tasks; do not pool unlike workloads into a claimed speedup.
Report observations against the declared thresholds, including inconclusive
results and the limits of quality, timing, and resource measurements. Separate
empirical observations from an Investigation's recommendation and from policy
adoption through the applicable maintainer decision process. Neither a plan
merge nor Evaluation completion adopts policy or authorizes another trial.

Preserve artifacts and protocol through the existing
[Work delivery commits](acceptance-tracing.md#work-delivery-commits) and
[PR evidence procedure](pull-requests.md), promoting lasting guidance to its
owner before cleanup. Git retains removed contracts and artifacts; PR and
linked execution records retain evidence. Do not add routine per-revision
bookkeeping, mandatory templates, or a second lifecycle.
