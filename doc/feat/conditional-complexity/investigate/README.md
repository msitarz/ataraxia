# Investigate condition complexity enforcement

## Purpose

Determine whether the latest stable complexipy release, a justified threshold,
and a complementary check can provide useful diagnostics and bounded adoption.

## Goals

- Establish the latest release's documented capabilities and limitations before
  practical assessment.
- Recommend justified limits or an evidence-backed capability-gap finding.
- Bound repair scope and Make/CI integration feasibility independently of policy
  delivery.

## Non-Goals

- Adopt policy, dependencies, or production repairs.
- Treat capability probes as production readiness or parent completion.
- Select or compare historical complexipy versions.

## Mechanisms

- Official complexipy documentation, release notes, and relevant release source
  provide the initial capability assessment.
- The latest stable complexipy release available at execution start supplies
  practical evidence for that exact version.
- The then-locked Ruff PLR0916 supplies the complementary Boolean-expression
  comparison.
- Existing Make routes, or the smallest temporary extension under owner review,
  run experiments.
- Retained findings distinguish documented claims, execution observations,
  assumptions, and missing evidence.

## Acceptance criteria

### **AC-1 DONE** Latest release capability is established

A documentation-first assessment establishes the latest release's capabilities
and limits, followed by bounded practical observations for the remaining ACs.

- The initial reading records the release version and date, assessment date,
  and relevant official documentation, release-note, and source references,
  including where current documentation differs from the assessed release.
- That reading explains documented commands, configuration, metrics, threshold
  semantics, diagnostics, and compatibility with Python 3.14, repository syntax,
  and supported platforms before experiments begin.
- Findings address Boolean chains, nesting, `elif`, structural `match`, simple
  and dense guards, quantifiers, and cohesive extraction using documentation
  and source first, with representative one-time observations where needed to
  resolve adoption questions rather than an exhaustive syntax matrix.
- Practical observations record commands, options, configuration, scores, exit
  statuses, diagnostics, and exact complexipy and locked Ruff versions.
- Findings distinguish documented claims from observed behavior and explain
  missed cases and false positives, including actual PLR0916 guard/expression
  coverage and the distinction between Boolean counts and function metrics.
- Unobserved compatibility and other missing evidence remain explicit with
  their causes; inability to obtain or run the latest release is a blocker or
  capability gap, not a reason to assess an older release.

### **AC-2 DONE** Threshold and scope have a justified recommendation

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
  [integrated readable-condition policy](../../../engineering.md#code-style).
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
  while one-time upstream-scoring and threshold probes are removed.
- Proposed retained adoption tests cover repository configuration and routing,
  rather than an upstream algorithm matrix.

A reviewed capability-gap finding can complete this Investigation while leaving
adoption blocked and the parent incomplete.

## Links

- [Official release listing](https://pypi.org/project/complexipy/),
  [usage guide](https://complexipy.com/usage-guide/),
  [changelog](https://complexipy.com/changelog/),
  [API reference](https://complexipy.com/api-reference/), and
  [source](https://github.com/rohaquinlop/complexipy) supply the initial
  reading.
- [Parent contract](../README.md) owns tooling scope and preservation
  boundaries.
- [Adoption Work](../adopt/README.md) consumes the independently reviewed
  findings.
- [Integrated engineering guidance](../../../engineering.md) owns the policy;
  this Investigation may proceed independently of adoption.
