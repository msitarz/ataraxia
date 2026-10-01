# Workflow Decision Records

Define a lightweight record for consequential decisions about the delivery
workflow. The record should capture context, the chosen direction, meaningful
alternatives, tradeoffs, consequences, and links to the PR or Works that carry
the decision. Current guidance remains authoritative in its existing owners;
a record explains why that guidance exists and how to reconsider it.

Completion means:

- State when a Workflow Decision Record (WDR) is useful, with a threshold that
  avoids records for minor wording edits or routine implementation choices.
- Define a numbered `doc/wdr/` collection, its index, and a concise format.
  Extract shared record syntax, status, numbering, amendment, and supersession
  conventions into one format owner used by both ADRs and WDRs. Keep
  architectural and workflow eligibility, routes, and indexes distinct; avoid
  refactoring unrelated ADR guidance.
- Add a conditional reading route for work that proposes or reviews a
  consequential workflow choice; do not make WDRs part of every task's startup
  reading.
- Include a retrospective shortlist of candidate decisions below. Label each
  as current guidance, an accepted decision, a pending Work, or an idea to
  evaluate. Do not imply that a candidate was separately approved, requires a
  WDR, or is fully implemented merely because related guidance exists.
- Explain how a decision record points to current guidance, how accepted
  choices are changed, and how implementation status is verified.
- On completion, update the parent README to `DONE` with the delivered outcome
  and remove this child directory in the same PR, following the Work lifecycle.

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
  [Structural review](../../../engineering.md#structural-review) folds
  structures with the same meaning, considers shared bases or helpers for
  variants, and moves code to the module that owns its responsibility.
- **Accepted for this planning effort:** WDRs record consequential workflow
  choices, preserve a short retrospective shortlist, and avoid bureaucracy for
  minor wording edits. This does not imply that every candidate above needs a
  WDR or that the shortlist contains a complete decision history.

This Work defines and records policy only; implementation of any newly proposed
workflow changes belongs to separately scoped Works.
