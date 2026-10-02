# Guidance consistency

Give fresh agents a consistent account of current rules, accepted decisions,
implemented behavior, and project commands.

The [WDR index](../../../../wdr/README.md) puts WDR 8 under proposals although
the record is accepted, and describes validation and acceptance tracing as
pending. WDR 7 remains proposed while its decision appears as current
[validation policy](../../../../validation.md). Reconcile these states using
available approval evidence or explicit maintainer resolution; implementation
alone must not be treated as approval.

The [architecture introduction](../../../../architecture.md) can be read as
making implementation authoritative when it conflicts with an ADR, contrary to
[documentation ownership](../../../../README.md). Clarify how actual behavior,
approved contracts, and deviations are represented.

Update the root README's direct CLI example to use the existing Make interface.
Resolve CONTRIBUTING's reference to an absent agent commit body structure
without inventing a new requirement.

## Acceptance

- **AC-1 DONE** The WDR index agrees with record statuses and current owner
  guidance; WDR 7 is explicitly accepted or identified as a candidate policy
  under evaluation, with the decision basis recorded in the delivery PR.
  Verification: compare the index, WDRs 7 and 8, and validation policy; inspect
  approval evidence or the maintainer's resolution.
- **AC-2 DONE** Guidance requires an implementation deviation from an approved
  contract to be surfaced rather than silently adopted as intended behavior.
  Verification: compare architecture and documentation ownership using a
  hypothetical implementation defect and a planned unimplemented decision.
- **AC-3 DONE** The root runnable example uses the documented Make target and
  contributor guidance has no dangling promise of a commit body structure.
  Verification: compare the example with the Make recipe and inspect the commit
  guidance; run Markdown formatting and local-link checks.

Resolve inconsistencies at their owners. Preserve accepted decision rationale
and avoid introducing additional templates or broader contribution policies.
