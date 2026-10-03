# 16. Use Evaluations for empirical evidence

Date: 2026-10-03

## Status

Proposed

## Context

The
[Evaluation workflow Work](https://github.com/msitarz/ataraxia/blob/f5f2e1e15ccb97899d2c21dee2f4109214e4109b/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/evaluation-workflow/README.md)
identifies reusable methods that otherwise disappear with local comparisons.
Investigation recommendations and Prototype feasibility results do not clearly
assign ownership of evidence from a declared empirical protocol.

## Decision

Propose Evaluation as a Work kind owning empirical evidence, with reusable
methods in [empirical evaluation guidance](../evaluation.md) and relationships
in [Work workflow](../workflow.md#evaluations). A specific Work and protocol own
the question, inputs, limits, thresholds, and observations. Keep the normal
Work lifecycle, review, and evidence procedures; allow independent Evaluations,
support for Investigations, and small inline comparisons.

Keeping all methods local avoids a new kind but loses discoverability after
cleanup. Putting them only under Investigation ties evidence to recommendations;
using Prototype conflates empirical comparison with implementation feasibility.
Mandatory templates or a separate evaluation lifecycle add maintenance without
improving the ownership boundary.

## Consequences

Reviewers can distinguish observations, recommendations, and adoption while
checking conditions, contamination, and missing measurements. Protocol detail
still scales to the question; no universal budget, model choice, threshold,
agent requirement, or trial authorization follows. This record remains a
proposal under the
[maintainer acceptance lifecycle](../decision-records.md#record-format); its
merge does not adopt a policy or complete an evaluation.
