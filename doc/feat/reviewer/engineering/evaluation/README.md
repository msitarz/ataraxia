# Engineering review evaluation

## Purpose

Produce bounded, inspectable evidence comparing engineering-review detection and
resource use across A/B/C strategies.

## Goals

- Measure instruction drift on realistic large engineering changes, including
  overlooked rules in deep and less prominent code.
- Compare detection quality and complete-strategy resource consumption fairly.
- Supply evidence for the engineering owner's granularity decision without
  adopting policy or requiring completed production delivery.

## Non-Goals

- Deliver the production reviewer, select its architecture, or adopt review
  policy.
- Require a formal statistical-power study unless the intended claims need one.
- Confound the primary comparison with cross-model or cross-effort studies.

## Inherited constraints

The [engineering parent](../README.md#inherited-constraints) and
[reviewer shared constraints](../../README.md#inherited-constraints) apply at
this Evaluation's boundary. A minimal experimental harness may run the
comparison before production implementation and granularity are finalized; it
need not satisfy every
[Delivery criterion](../delivery/README.md#acceptance-criteria). This is no
exemption from applicable immutable-input, read-only, bounded-resource,
provenance, withheld-label and prior-answer separation, or failure-accounting
guarantees. The maintainer accepts the CLI declarations and automatic context
limitation defined at the
[protocol boundary](protocol.md#cli-invocation-boundary-and-accepted-limitation);
this does not establish tool-free operation or waive those retained protections.
AC-3 verifies them locally; engineering and reviewer owners retain their
integration guarantees.

For this experiment only, process cleanup has the owned-group scope and
explicit upstream lifecycle assumption in the
[process supervisor contract](process-supervisor/README.md#additional-context).
That contract owns lifecycle details; this qualification does not weaken
production delivery requirements.

[Empirical evaluation guidance](../../../../evaluation.md) owns general protocol
declaration, isolation, independent repetitions, failure and stop handling,
retention, and interpretation. The criteria below add this comparison's concrete
requirements rather than replace those rules.

## Acceptance criteria

### **AC-1 TODO** A declared comparison supports bounded, fair claims

Before trial outcomes, an inspectable protocol defines the comparison and its
completion conditions under the linked empirical evaluation guidance.

The primary comparison includes:

- A: the complete applicable rule list in one whole-diff session, explicitly a
  multi-rule comparator outside the single-criterion production-job invariant.
- B: independent whole-diff sessions, each assessing one rule.
- C: independent changed-function sessions, each assessing one applicable rule.

The protocol fixes these experiment-specific conditions:

- Frozen realistic, sufficiently large diffs derived from classified historical
  engineering incidents, with known seeded violations at varied depths and
  locations, including deeply nested and less prominent code, plus realistic
  compliant cases for false-positive measurement.
- Owner-validated withheld reference labels mapping incident classes, rules,
  seed locations, expected detections, and compliant cases.
- Matched model, reasoning effort, applicable rule set, source material, and
  permitted references and review conditions, with intended granularity and
  prompt/context differences explicit.
- Eligibility for additions, deletions, non-function changes, and broader-scope
  rules; equivalent-coverage comparisons use a common expected-detection
  denominator, with narrower eligibility and exclusions reported separately.
- Independent incident/seed diversity distinguished from repeated model sessions
  on the same cases, with case counts and coverage per rule; unsupported
  per-rule conclusions remain exploratory rather than generalizing repeated
  sessions to new incidents.
- A budget and stopping rules for reference labeling, manual finding
  adjudication, and deduplication, preferring complete adjudication of a bounded
  workload.
- If adjudication is sampled, a declared sampling design, appropriate precision
  estimation, and explicit limitations; oversampled seed-associated findings are
  not treated as representative of all findings.
- An inconclusive-result fallback and evidence required to call that fallback
  viable, declared before observing outcomes.

An optional secondary model/effort generalizability study remains separate from
the common-model, common-effort primary comparison. No strategy is chosen here.

### **AC-2 TODO** Retained observations support quality and resource conclusions

The report supplies inspectable matched A/B/C observations, including manual
owner validation, without overstating generality or measurement availability.

- Bounded preparation establishes what usage telemetry the actual invocation
  exposes before committing the full trial budget; its observations and limits
  are retained rather than assuming telemetry from another invocation.
- Recall, precision, token consumption, and elapsed time have separate evidence
  with declared denominators, units, methods, and timing boundaries.
- Resource measurements cover a complete strategy run, including all constituent
  B or C sessions, rather than comparing one isolated job with the full A run.
- Observed usage, estimates, and unavailable measurements remain distinct;
  unknown usage stays unknown, permitting bounded quality or timing conclusions
  but no unsupported detection-per-token or cost claims.
- Owner adjudication validates and deduplicates reported findings against the
  common rubric, records observed owner effort, and respects the declared human
  budget, stopping rules, and any sampling limitations.
- The report includes case counts, coverage per rule, eligibility and
  exclusions, failures and deviations, and limits on incident diversity and
  per-rule claims.
- Effectiveness relative to consumed resources is assessed only where evidence
  supports it, retaining separate recall, precision, and latency; focused review
  may consume more tokens, and lowest consumption alone is not success.

Protocol and observations are retained under the linked evaluation guidance for
independent review. The result informs the
[engineering owner's decision](../README.md#ac-7-todo-granularity-follows-representative-detection-evidence);
Evaluation completion does not select or adopt production policy.

### **AC-3 TODO** Experimental execution verifies its applicable guarantees

The experimental boundary preserves safety and evidence validity without relying
on unverified production behavior or treating failures as detections.

Concrete verification at the actual harness boundary establishes:

- Immutable source and guidance, traceability to exact supplied prompts, inputs
  and settings, retained observable context and disclosed opaque
  automatic-context limits, stable plans/identities for identical inputs,
  separation for changed inputs, and isolation from withheld labels and prior
  answers.
- Pre-execution job/token estimates and visible budget refusal, finite
  concurrency, timeout, output and retry limits, and cleanup after success,
  failure, timeout, or cancellation under the
  [experimental process guarantee](process-supervisor/README.md#acceptance-criteria).
- Actual harness wiring to the supervisor's public stop hook, with stop latched
  before fallible evidence recording and checked before every dispatch.
- `SIGINT`, `SIGTERM`, and task cancellation stop new calls, clean up the active
  invocation, and end evaluation without retry; `SIGKILL` cannot execute
  cleanup.
- Unsafe signal/wait cleanup or uncertain acquisition marks the run incomplete
  and forbids further dispatch independently of the ordinary infrastructure-
  failure threshold.
- The caller owns the protocol's optional retries and starts another attempt
  only after prior cleanup permits dispatch, without overlapping an unstopped
  direct CLI; the supervisor performs no hidden retries.
- Active-call failure and cleanup evidence remain inspectable, and every planned
  but undispatched call retains not-started accounting, including recording
  failures after stop is latched.
- Read-only source and refs under successful, failing, and attempted-write runs;
  a prompt instruction alone does not prove enforcement.
- Accounting for every planned session, with failed, missing, timed-out,
  malformed, duplicate, stale, or foreign output never counted as successful
  coverage, and uncertainty and non-applicability kept distinct from passes.
- Deterministic aggregation of identical validated results irrespective of
  session completion order, preserving evidence correspondence; any cached
  observations respect complete effective-input identity and never count as
  independent trials.

Controlled process-boundary checks exercise those success and failure conditions
in disposable environments; actual invocation observations establish integration
and what telemetry is available. Evidence identifies what each method proves and
its limits under [testing guidance](../../../../testing.md). The baseline's
multi-rule prompt changes no other applicable shared guarantee; the accepted
CLI limitation is disclosed under the protocol rather than claimed as verified
isolation.

## Children

- DONE [Experimental CLI process supervisor](process-supervisor/README.md):
  Provide bounded CLI invocation for the engineering-review experiment without
  requiring a production reviewer runner.

## Links

- [Comparison protocol](protocol.md) compares A/B/C on fixed static
  inputs, including prepared function/context packets, with the declared CLI
  limitation, retained boundary protections, raw and adjusted token accounting,
  budgets and thresholds for owner review; a separately reported
  effort analysis reuses the common-medium primary observations.
- [Engineering review](../README.md) owns the recorded decision and integrated
  delivery; [Engineering reviewer delivery](../delivery/README.md) depends on
  this completed evidence and that decision.

## Additional context

The supporting protocol starts with a bounded static PASS/VIOLATION comparison
of all three A/B/C strategies at medium effort, with a separate matched
none/low/medium/high effort analysis on the same inputs. Function/context
extraction happens during preparation and requires no production reviewer. The
initial corpus does not complete the historical/diversity evidence required
above or support a production granularity decision. Actual prepared sources,
private labels, runtime binding, retained boundary evidence, and matched input
baselines remain unprepared and require the protocol's later authorization and
freeze gates. The accepted CLI limitation is not evidence that these
requirements have been satisfied. This definition executes no telemetry
preparation, experimental wrapper, trial,
production architecture or implementation. All acceptance criteria remain TODO.
