# Workflow Decision Records

Establish a lightweight way to record consequential decisions about the
delivery workflow and inventory the findings that may inform those decisions.
Keep current guidance in its authoritative owner; records preserve rationale
and point to that guidance. The inventory describes evidence and status without
turning each finding into an accepted decision.

## Works

- **DONE** [Create the WDR workflow](../../../wdr-workflow.md): established
  eligibility, routing, and lifecycle, with a shared
  [ADR/WDR record format](../../../decision-records.md) and [WDR
  index](../../../wdr/README.md).
- **TODO** [Inventory workflow findings](inventory/README.md): classify the
  existing findings and candidate decisions, then select and record qualifying
  retrospective WDRs without implying that every candidate needs one.

Complete the workflow child before the inventory child so the inventory can use
the established record policy. On each child delivery, update its entry to
`DONE` with the outcome and remove that child directory in the same PR. Once
both children are complete, update the enclosing
[reviewable workflow map](../README.md) to `DONE` and remove this parent
directory in that delivery PR, following the
[Work lifecycle](../../../workflow.md).

This planning Work defines its children only; it does not implement the WDR
workflow or apply the inventory findings to current guidance.
