# Investigate condition complexity enforcement

## Purpose

Determine which supported complexipy version, threshold, and complementary
condition rule can deliver the [parent outcome](../README.md) with useful
diagnostics and bounded repairs.

## Goals

- Establish candidate capability and compatibility from pinned-version evidence.
- Recommend justified adoption settings or an evidence-backed capability-gap
  finding.
- Bound adoption feasibility and identify any unresolved repairs or integration
  requirements.

## Non-Goals

- Adopt policy, dependencies, or production-source repairs.
- Treat a successful capability probe as production readiness or parent
  completion.

## Mechanisms

- A concrete complexipy candidate supplies observed function-level
  cognitive-complexity behavior.
- Pinned Ruff 0.16.8 PLR0916 supplies the complementary Boolean-expression
  comparison.
- Make runs project-tool experiments through its existing boundary or the
  smallest temporary extension under owner review.
- Retained comparison artifacts distinguish observed results from assumptions
  and unresolved capability gaps.

## Acceptance criteria

### **AC-1 TODO** Pinned candidate capability is established

A reviewable comparison establishes the candidate's capabilities and limits
against the [parent seed](../README.md#seed-and-planning-baseline) and
[shared boundaries](../README.md#mechanisms).

- Official release and source references and observed pinned-version checks
  establish the exact complexipy version and whether it is compatible with
  Python 3.14, repository syntax, and supported platforms.
- Recorded options, configuration, commands, scores, exit statuses, and
  diagnostics identify what was observed for the candidate and pinned Ruff.
- Capability checks address Boolean chains, nesting, `elif`, structural `match`,
  simple and dense guards, quantifiers, and cohesive extraction, with
  unavailable observations and their causes stated explicitly.
- The comparison explains missed cases and false positives, including PLR0916's
  actual coverage of guards and expressions.
- Function cognitive complexity and Boolean counting remain distinct, and
  current online documentation does not substitute for pinned-version evidence.
- Any unsupported requirement is a concrete blocker requiring steering rather
  than an assumed capability.

### **AC-2 TODO** Threshold and scope have a justified recommendation

A short recommendation identifies either a supported adoption direction or an
evidence-backed capability gap suitable for independent review.

For a supported fit, the recommendation establishes the following outcomes.

- A baseline score distribution and concrete high-score functions cover the
  existing lint scope, including source, scripts, tests, and examples.
- Readability judgments on the seed, simple counterexamples, and the necessary
  repair inventory justify the threshold rather than the default 15 or a value
  raised merely to pass.
- The comparison considers whether complete consumed-record validation and typed
  pure decisions remove the seed's dense conditions.
- Observed below-threshold, exact-threshold, and above-threshold outcomes
  establish the proposed blocking semantics.
- Precise scope, exceptions, and diagnostic format account for capability gaps
  and remaining manual review obligations.
- Discovery excludes transient environments, caches, and build output
  consistently with existing lint discovery without exempting tests or scripts
  wholesale.

A capability-gap recommendation identifies concrete blockers, missing
observations, and unchecked consequences without inventing feasible thresholds,
scope, or repairs. The finding includes the experiments needed to establish the
gap; unavailable observations do not excuse those experiments.

### **AC-3 TODO** Adoption feasibility is bounded

For a supported fit, the recommendation bounds the necessary repairs and
smallest Make/CI integration for the adoption Work; a capability-gap finding
identifies which integration and repair questions remain unresolved.

- The integration supports focused path arguments and full CI within the
  existing Make boundary, whose `ARGS` inputs accept paths rather than arbitrary
  options.
- Any temporary Make extension needed for experiments is the smallest route
  under owner review.
- One-time probe code and observed results remain recoverable in Git and the
  comparison under [test ownership](../../../test-ownership.md), while temporary
  upstream-scoring probes are removed.
- Proposed retained adoption tests cover repository configuration and routing
  rather than an upstream algorithm matrix.
- A capability-gap finding may complete this Investigation while leaving
  adoption blocked and the parent incomplete.

## Links

- [Parent contract](../README.md) owns the frozen seed, shared guidance and
  preservation boundaries, and adoption constraints.
- [Adoption Work](../adopt/README.md) consumes the independently reviewed
  recommendation.
