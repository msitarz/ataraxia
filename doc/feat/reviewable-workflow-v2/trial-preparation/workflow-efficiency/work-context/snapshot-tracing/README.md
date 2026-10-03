# Acceptance snapshot tracing

Investigate whether an optional `pytest.mark.covers` SHA reference is useful
when a completed Work contract is removed, or whether current no-change
behavior is preferable. This is an
[Investigation](../../../../../../workflow.md#investigations), not authorization
to adopt a marker or change acceptance policy. It follows
[completion routing](../completion-routing/README.md) and the
[context tool](../context-tool/README.md). Coordinate any owner implications
with [PR evidence](../../pr-evidence/README.md) and
[handoffs](../../handoffs/README.md); do not rewrite their contracts.

## Acceptance

- **AC-1 TODO** The Investigation compares no change with an optional snapshot
  reference using existing acceptance collection, checking, and selection
  tools, and identifies whether those tools can use a contract SHA after its
  path is removed.
  Validation: run or inspect the existing acceptance tooling against a
  retained and removed-contract scenario, recording the exact commands or
  source paths examined and observed behavior.
- **AC-2 TODO** The comparison addresses preservation of Work and AC selection,
  rejection of unknown SHA, path, or AC values, self-reference, rebases and
  reachability, and limits marker metadata so it cannot establish `DONE` or
  current test success.
  Validation: evaluate each listed case against the existing checker and
  selector behavior or a bounded proposed behavior, recording observed facts
  separately from assumptions.
- **AC-3 TODO** The recommendation states tradeoffs, unresolved questions, and
  a clear change, no-change, or inconclusive outcome without adopting behavior
  or claiming historical provenance proves completion or current test
  success.
  Validation: compare the recommendation with the evidence and uncertainty
  recorded for AC-1 and AC-2.
