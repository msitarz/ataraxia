# Engineering review

## Purpose

Let a parent agent obtain focused engineering judgments for a change with
explicit coverage and evidence.

## Goals

- Make the `reviewer` skill usable for engineering review from change selection
  to a concise parent report.
- Review changed functions against applicable semantic engineering rules without
  duplicating reliable deterministic checks.
- Expose uncertain judgments, scope gaps, and execution failures for owner
  review.

## Non-Goals

- Deliver test-specific, architecture, or guidance review.
- Judge every engineering rule at function scope or claim that all combinations
  of functions and rules are applicable.
- Automate corrections, owner reconciliation, acceptance, or merge decisions.

## Inherited constraints

All [reviewer shared constraints](../README.md#inherited-constraints) apply.
This child verifies its complete invocation-to-report flow and local resource
and failure behavior; the parent owner verifies integrated guarantees and future
domain design fit under the parent's criteria.

## Acceptance criteria

### **AC-1 TODO** Parent invocation selects a traceable review scope

A parent agent can invoke the `reviewer` skill for an identified set of changes
and receive a report attributable to the intended source and comparison.

- Given a supported change selection, invocation records the selected source,
  comparison, effective model, reasoning effort, concurrency and resource
  bounds, and evidence location before reporting judgments.
- Unsupported or ambiguous selections, unavailable source, and invalid settings
  produce an actionable refusal or incomplete report without claiming review
  success.
- Dirty inputs, if supported, have an immutable identity covering their actual
  contents; otherwise they are refused explicitly before reviewing another
  revision by mistake.
- An empty selection is reported as no selected changes, distinct from reviewed
  changes with no violations.

### **AC-2 TODO** Coverage reflects subjects and applicable semantic rules

The review plan identifies changed functions and derives applicable criteria
from existing engineering guidance with inspectable reasons for scope decisions.

- Changed functions are the primary subjects, including relevant methods and
  nested or asynchronous functions in the supported source scope.
- The plan identifies the source scope it supports and accounts for additions,
  modifications, deletions, non-function changes, and discovery failures without
  silently treating undiscovered material as reviewed.
- Criteria are traceable to authoritative guidance and its reviewed revision;
  deterministic-tool exclusions are justified against current configuration and
  the rule portion actually enforced.
- A rule's semantic requirements remain eligible when a deterministic metric
  checks only a related signal, such as complexity or statement count.
- Selection considers applicability rather than scheduling a blind Cartesian
  product; exclusions and unresolved applicability remain inspectable.
- Rules needing broader scope are supplied that scope where supported, or
  reported as requiring owner or other-domain review rather than forced into a
  function judgment or silently omitted.
- Test-specific rules are explicitly outside this domain, with scope gaps
  visible for changes involving tests.

### **AC-3 TODO** Each independent judgment has sufficient focused context

Every planned job evaluates exactly one identified subject against one criterion
and returns a structured judgment using the existing focused-review vocabulary.

- The prompt identifies the criterion and subject, supplies relevant old and new
  source and necessary caller, type, and module context, and avoids unrelated
  material.
- The reviewer can return `UNCERTAIN` with the missing context or ambiguity;
  context assembly failures do not fabricate semantic results.
- `VIOLATION` includes concrete source evidence and its consequence;
  `NOT_APPLICABLE` explains its reason, and findings remain separate from
  optional suggestions.
- `PASS` means adequate context supports no violation of this one criterion;
  sound code needs no finding or refactor quota.

### **AC-4 TODO** Reviews execute with bounded read-only resources

The Python runner executes independent non-interactive `codex exec` sessions
using the selected model and reasoning effort within declared finite limits.

- Given more jobs than available slots, observed simultaneous sessions never
  exceed the configured positive limit.
- Given a hung session, excessive output, launch failure, or parent
  cancellation, the runner finishes or cancels under its declared bounds,
  accounts for unfinished work, and releases its acquired resources and child
  processes.
- A reviewer cannot modify reviewed repository files or refs; successful,
  failing, and attempted-write runs preserve the reviewed source.
- Limits and read-only behavior are verified through the actual process
  boundary; a prompt instruction alone does not establish enforcement.

### **AC-5 TODO** Aggregation cannot hide failed or unresolved coverage

The parent receives deterministic accounting of all planned jobs and a concise
report with violations, uncertainties, and coverage linked to retained evidence.

- Valid structured results preserve `PASS`, `VIOLATION`, `NOT_APPLICABLE`, and
  `UNCERTAIN` separately without converting uncertainty or non-applicability
  into a pass.
- Failed, timed-out, missing, malformed, duplicate, stale, and foreign results
  remain visible with reasons and cannot count as successful coverage.
- A mixture of valid and invalid results retains valid judgments and reports the
  missing coverage; a successful process exit alone is insufficient.
- Results cannot be reassigned to another job, criterion, subject, or revision;
  source drift or inconsistent context is rejected or reported incomplete.
- Permuting completion order leaves the same aggregate judgments, coverage, and
  report ordering for the same validated inputs.
- A report with no violations distinguishes complete supported coverage,
  unresolved semantic uncertainty, exclusions, and incomplete execution.
- The owner can inspect each job's inputs, criterion provenance, settings,
  judgment or failure, and source evidence from the report without relying on
  an untraceable summary.

### **AC-6 TODO** Verification observes behavior at the owning boundaries

Evidence establishes the delivered skill flow, deterministic accounting, process
safety, and stated limits without claiming that fixed fake responses establish
LLM semantic accuracy.

Independent review assesses scenarios and assertions under
[testing guidance](../../../testing.md), using the smallest boundary that can
observe each guarantee:

- Controlled judgments exercise all four outcomes and mixed-result aggregation,
  malformed and missing output, duplicates, identity mismatch, source drift,
  launch failure, timeout, cancellation, and resource exhaustion.
- Real process-boundary tests in disposable environments observe concurrency,
  cleanup, read-only preservation, settings propagation, and report/evidence
  correspondence without requiring live network access or wall-clock sleeps.
- Representative source changes exercise discovery, applicability exclusions,
  broader-context needs, and empty or unsupported selections through the real
  selection-to-report path.
- A bounded live `codex exec` invocation demonstrates actual non-interactive
  integration, structured-output compatibility, and model/effort selection;
  unavailable tooling, credentials, or skipped execution is an evidence gap.
- Live judgments are independently inspected against the supplied subject,
  criterion, and context, with their semantic limits stated; repeatable output
  across LLM runs and universal rule accuracy are not promised.

## Links

- [Reviewer](../README.md) owns shared requirements, the complete vision, domain
  deferrals, and unresolved typed architecture questions.
- [Engineering review](../../../engineering-review.md) owns judgment meanings
  and responsible-owner reconciliation.
- [Engineering conventions](../../../engineering.md) and
  [tool configuration](../../../../pyproject.toml) distinguish semantic guidance
  from configured deterministic checks.

## Additional context

This child is actionable as one useful engineering-review delivery; its internal
responsibilities are not separate delivery layers. Typed architecture must check
its actual reviewability and any independently useful split under the parent's
[decomposition constraints](../README.md#additional-context). This definition
does not choose a schema, subprocess API, criterion inventory, module layout,
or context algorithm.
