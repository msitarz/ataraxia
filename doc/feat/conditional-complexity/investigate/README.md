# Investigate condition complexity enforcement

Which supported complexipy version, threshold and complementary condition rule
deliver the [parent outcome](../README.md) with useful diagnostics and bounded
repairs? Produce a small recommendation; this Work does not adopt policy or
repair production source. The parent's frozen seed and preserved behavior are
the shared context.

Select a concrete candidate using official release/source documentation and
verify compatibility with Python 3.14, repository syntax and supported
platforms. Record exact version, options/configuration, commands, scores, exit
statuses and diagnostics. Current online documentation is not pinned-version
evidence. Test Boolean chains, nesting, `elif`, structural `match`, simple and
dense guards, quantifiers and cohesive extraction; explain missed cases and
false positives. Check pinned Ruff 0.16.8 PLR0916 as a complement, including its
actual coverage of guards and expressions. Do not treat Boolean counting and
function cognitive complexity as interchangeable.

Inspect a baseline score distribution and concrete high-score functions within
the existing lint scope, including source, scripts, tests and examples. Select a
threshold from readability judgments on the seed, simple counterexamples and the
necessary repair inventory, including whether a complete consumed-record
boundary and typed pure decisions remove the seed's dense conditions, rather
than adopting the default 15 or raising it just to pass. Propose precise scope,
exceptions, diagnostic format and blocking semantics; show below-threshold,
exact-threshold and above-threshold outcomes. Exclude transient environments,
caches and build output consistently with existing lint discovery; do not exempt
tests or scripts wholesale.

Describe the smallest Make integration supporting focused path arguments and
full CI. Run project-tool experiments through Make only; existing `ARGS` inputs
accept paths, not arbitrary options. If experiments require a route, define the
smallest temporary Make extension under owner review. Preserve one-time probe
code/results in Git and the comparison, then remove probes of upstream scoring
under [test ownership](../../../test-ownership.md). Retained adoption tests own
our configuration and routing, not an upstream algorithm matrix.

- **AC-1 TODO** A short reviewable recommendation identifies a compatible pinned
  complexipy candidate, justified threshold/scope/exceptions and observed
  scoring/failure behavior, evaluates complementary PLR0916 and manual guidance,
  and bounds adoption repairs and the normal Make/CI integration. Any
  unsupported requirement is stated as a concrete blocker requiring steering.

  Validation: independently review official release/source references, exact
  candidate and Ruff evidence, observed Make probes, baseline distribution and
  representative readable/dense examples against the parent seed and behavior.
  Inspect exact-threshold results, guard/quantifier gaps, false positives and
  necessary repairs. Run documentation and acceptance checks. A capability-gap
  finding may complete this Investigation, but cannot complete the parent.
