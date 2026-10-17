# Investigate condition complexity enforcement

## Purpose

Determine which supported complexipy version, threshold, and complementary check
can provide useful diagnostics and bounded adoption.

## Goals

- Establish candidate capability and compatibility through pinned-version
  evidence.
- Recommend justified limits or an evidence-backed capability-gap finding.
- Bound repair scope and Make/CI integration feasibility independently of policy
  delivery.

## Non-Goals

- Adopt policy, dependencies, or production repairs.
- Treat capability probes as production readiness or parent completion.

## Mechanisms

- A pinned complexipy candidate supplies observed cognitive-complexity behavior.
- The then-locked Ruff PLR0916 supplies the complementary Boolean-expression
  comparison.
- Existing Make routes, or the smallest temporary extension under owner review,
  run experiments.
- Retained findings distinguish observations, assumptions, and missing evidence.

## Acceptance criteria

### **AC-1 TODO** Pinned candidate capability is established

A bounded comparison establishes the exact candidate's capabilities and limits.

- Official release/source references and observed checks establish the selected
  version's compatibility with Python 3.14, repository syntax, and supported
  platforms.
- Commands, options, configuration, scores, exit statuses, and diagnostics
  identify what was observed for the candidate and pinned Ruff.
- Checks address Boolean chains, nesting, `elif`, structural `match`, simple
  and dense guards, quantifiers, and cohesive extraction.
- Findings explain missed cases and false positives, including actual PLR0916
  guard/expression coverage, distinguishing Boolean counts from function
  metrics.
- Missing observations and their causes remain explicit; current documentation
  does not substitute for pinned-version evidence or support unobserved claims.

### **AC-2 TODO** Threshold and scope have a justified recommendation

A short recommendation identifies a supported adoption direction or a concrete
evidence-backed capability gap.

- A baseline distribution and representative high-score functions cover existing
  lint scope, including source, scripts, tests, and examples.
- Readability judgments and the necessary repair inventory justify the threshold
  rather than accepting a default or raising it merely to pass.
- Observed below-, exact-, and above-threshold behavior establishes proposed
  blocking semantics.
- Precise scope, exceptions, diagnostics, and remaining manual review
  obligations reflect observed capabilities and the
  [proposed readable-condition policy](../../validated-core/README.md#ac-6-todo-readable-decision-logic).
- Discovery excludes transient environments, caches, and build output
  consistently with lint discovery, without blanket exemptions for scripts or
  tests.

A capability-gap recommendation records the experiments establishing the gap,
missing observations, and unresolved consequences rather than inventing feasible
thresholds, scope, or repairs.

### **AC-3 TODO** Adoption feasibility is bounded

The recommendation bounds necessary repairs and the smallest Make/CI
integration, or identifies which questions a capability gap leaves unresolved.

- Integration supports focused path arguments and full CI through existing Make
  boundaries, with `ARGS` accepting paths rather than arbitrary options.
- Repairs are assessed against the
  [parent preservation boundary](../README.md#shared-preservation-boundary).
- Temporary experimental integration stays minimal; probe methods and observed
  results remain recoverable under [test ownership](../../../test-ownership.md)
  while one-time upstream-scoring probes are removed.
- Proposed retained adoption tests cover repository configuration and routing,
  rather than an upstream algorithm matrix.

A reviewed capability-gap finding can complete this Investigation while leaving
adoption blocked and the parent incomplete.

## Links

- [Parent contract](../README.md) owns tooling scope and preservation
  boundaries.
- [Adoption Work](../adopt/README.md) consumes the independently reviewed
  findings.
- [Validated core guidance](../../validated-core/README.md) owns proposed
  policy; this Investigation may proceed independently of its integration.
