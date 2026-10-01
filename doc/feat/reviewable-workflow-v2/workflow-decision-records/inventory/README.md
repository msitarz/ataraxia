# Inventory workflow findings

Classify the existing findings and candidate decisions that may inform
Workflow Decision Records. Preserve the distinctions between current guidance,
accepted decisions, pending Works, and ideas to evaluate. Do not imply that a
candidate was separately approved, requires a WDR, or is fully implemented
merely because related guidance exists.

Completion means:

- Preserve the findings and candidate decisions below, updating their labels
  only when checked evidence supports the change.
- Link each current rule to its authoritative owner and each pending item to
  its Work. Keep current guidance in its owner and WDRs as the rationale owner.
- After the WDR policy is established, select findings that meet its
  consequential-decision threshold and write an initial retrospective set of
  WDRs. Explain the selection; do not create a record for every candidate or
  imply that a candidate was separately approved.
- Link to permanent WDR policy documents, not this planning Work's temporary
  child README. On completion, update this Work's parent map to `DONE` with the
  delivered outcome and remove this child directory in the same PR, following
  the [Work lifecycle](../../../../workflow.md).

Findings and candidate decisions:

- **Current contribution contract:** Small delivery increments sized for
  roughly five minutes of human review; the maintainer steers each iteration
  and performs manual merge.
- **Current Work contract:** A Work is identified by its directory path and
  short README contract; additional specification or design files are optional,
  with no mandatory YAML or journal.
- **Current Work contract:** Parent maps own immediate-child TODO, DONE, and
  ABORT status; nesting beyond five levels is strongly discouraged.
- **Current contribution contract:** Work PRs target `master` by default, with
  another base only by explicit instruction. Routine issue tracking is
  unnecessary for Works; issues remain available for bugs and human
  collaboration.
- **Current Work contract:** PR discussion and Git preserve review history.
  Promote lasting rules to their owners, then remove completed Work artifacts
  rather than accumulating journals or result-SHA loops.
- **Current documentation and tool contracts:** Guidance has one owner and a
  focused conditional reading route. A link alone does not require recursively
  reading its target. `make help` discovers tools and the Makefile owns
  executable commands.
- **Accepted for this Work; current after delivery:** Compact Markdown source
  tables reduce width-driven whole-table diffs, at the cost of source columns
  no longer aligning. The maintainer explicitly chose this, reversing the
  previous aligned-table preference.
- **Pending Work:** Focused development checks and the full CI merge gate. The
  draft-and-merge-checks Work is still pending; do not report its policy as
  adopted.
- **Completed tooling Works:** `rumdl` formatting and offline link checks are
  adopted through Make targets with CI parity. The tool investigation and
  checker integration Works are both marked `DONE`.
- **Pending Work:** Stable acceptance-criterion IDs scoped to their owning
  file; `pytest.mark.covers` keyword lookup; and the distinction between
  TODO/DONE coverage and passing/review status. The acceptance-traceability
  Work remains pending.
- **Current test-ownership contract:** Retain project integration contracts
  and concrete regression tests; remove upstream-only probes with one-time
  PR/Git evidence.
- **Current Work contract:** An Investigation recommends from checked evidence
  and uncertainty; a Prototype answers a bounded question through exploratory
  implementation.
- **Current Work contract:** Mermaid is optional and useful when a diagram
  clarifies behavior or relationships; assess whether a human visual review
  rule adds value.
- **Current branch-cleanup contract:** The focused post-merge procedure
  protects dependencies, dirty state, and undelivered commits.
- **Current engineering contract:**
  [Structural review](../../../../engineering.md#structural-review) folds
  structures with the same meaning, considers shared bases or helpers for
  variants, and moves code to the module that owns its responsibility.
- **Accepted for this planning effort:** WDRs record consequential workflow
  choices, preserve a short retrospective shortlist, and avoid bureaucracy for
  minor wording edits. This does not imply that every candidate above needs a
  WDR or that the shortlist contains a complete decision history.

This Work records a bounded retrospective selection only; it does not approve
or implement the listed policies.
