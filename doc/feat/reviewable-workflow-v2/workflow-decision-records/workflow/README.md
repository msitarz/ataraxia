# Create the WDR workflow

Define a lightweight record and workflow for consequential delivery-workflow
decisions. A WDR captures context, the chosen direction, meaningful
alternatives, tradeoffs, consequences, and links to the PR or Works that carry
the decision. Current guidance remains authoritative in its existing owners; a
WDR explains why guidance exists and how to reconsider it.

Completion means:

- State when a WDR is useful, with a threshold that avoids records for minor
  wording edits and routine implementation choices.
- Define a numbered `doc/wdr/` collection, its index, and a concise record
  format. Establish one shared owner for ADR/WDR record syntax, status,
  numbering, amendment, and supersession conventions. Keep architectural and
  workflow eligibility, routes, and indexes distinct; avoid refactoring
  unrelated ADR guidance.
- Add a conditional reading route for work that proposes or reviews a
  consequential workflow choice. Do not make WDRs part of every task's startup
  reading.
- Explain how a WDR points to current guidance, how accepted choices are
  changed, and how implementation status is verified. Keep guidance ownership
  separate from the rationale recorded in WDRs.
- Establish permanent policy documents and routes that the inventory can use
  after this child Work is removed. On completion, update this Work's parent
  map with the permanent policy owner and delivered outcome, then remove this
  child directory in the same PR, following the
  [Work lifecycle](../../../../workflow.md).

The companion findings inventory depends on this workflow and must be reviewed
after it. This Work establishes the WDR policy; it does not carry out the
inventory, write retrospective WDRs, or apply/adopt the candidate findings.
