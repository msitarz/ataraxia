# Workflow Decision Records

Read when proposing, recording, or reviewing a consequential decision about
the repository's delivery workflow. The [shared decision record
format](decision-records.md) owns syntax, numbering, status, and amendment or
supersession conventions.

## When to record a decision

Write a WDR when a choice establishes or materially changes a delivery rule
that future Works need to understand, such as Work lifecycle, delegation,
review gates, maintainer control, or cross-Work scope and sizing. A WDR keeps
the rationale for a consequential choice available for later reconsideration.
Do not create one for minor wording edits, routine implementation choices, or
changes that simply bring behavior into line with accepted guidance.

## Record and maintain decisions

1. Search the [WDR index](wdr/README.md) and inspect the authoritative guidance
   owners affected by the proposed choice.
2. Write a numbered record under `doc/wdr/` using the shared format. Include
   links to affected guidance and the PR or Work that carries the change.
3. Update current rules in their authoritative owner. A WDR preserves rationale;
   it does not replace the current guidance or approve its own implementation.
4. Verify delivery status from the current owner and relevant PR, Work, or
   implementation evidence. An `Accepted` WDR alone does not mean the guidance
   or implementation is complete.
5. Follow the shared lifecycle when amending or superseding a record. Update
   the WDR index when records are added or changed.
