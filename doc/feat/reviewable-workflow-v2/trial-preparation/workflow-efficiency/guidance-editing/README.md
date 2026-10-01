# Guidance editing

Strengthen the existing
[documentation review owner](../../../../../README.md#review) to require
reviewing the surrounding section and directly related rules as a whole when
changing guidance. Existing rules already check ownership, duplication, and
cohesive scope; recent #107 and #108 reviews showed that repeated explanations
can remain when edits focus only on their target paragraphs.

Promote lasting guidance only in `doc/README.md#review`. Do not add a separate
guidance file, mandatory template, checklist, journal, word-count target, or a
WDR for routine clarification. Integrate new rules where they belong, remove
repeated explanations within an owner, and replace cross-owner repetition with
pointers. Retain distinct exceptions, examples, and explanation needed to
understand the behavior, along with every substantive requirement, reading
route, and anchor. This is not a blanket terseness goal and does not authorize
semantic changes or edits to accepted WDR history.

Apply the review to bounded examples after their related Works are integrated:
the repeated return, recovery, scope, and correction-loop explanations in
[#107](https://github.com/msitarz/ataraxia/commit/c48b3663e32c59862ef7cfc5b761fc6a9fcdbd8e),
and the acceptance TODO/DONE, CI, declaration, and criterion-retention
explanations in
[#108](https://github.com/msitarz/ataraxia/commit/2bbdd12d8fd39827b8f5650a6db0f211e3ee325f).
Coordinate affected owners and bounded snippets with
[Handoffs, PR evidence, and tree orchestration](../README.md#works) before
shared-owner edits. Sequence actual overlaps; the `doc/README.md` clarification
does not need a global dependency on unrelated children. If examples exceed
quick review, split rather than broaden this leaf.

## Acceptance

- **AC-1 TODO** The existing review owner explicitly requires a whole-section
  pass over the affected surrounding content and directly related rules.
  Verification: inspect the updated `doc/README.md#review` rule and walk
  through a guidance change that also affects a neighboring explanation.
- **AC-2 TODO** A bounded consolidation preserves identifiable requirements,
  routes, anchors, and distinct useful examples while removing repetition in
  the #107 and #108 scenarios.
  Verification: after the referenced Works are integrated, trace the
  return/recovery and acceptance-evidence scenarios before and after editing,
  including a pending manual criterion and a completed return.
- **AC-3 TODO** The updated guidance and examples retain valid local links and
  explanations of CI, declarations, approval, and recovery without relying on
  word-count reduction or changing accepted decisions.
  Verification: run the documentation checks and walk the relevant reading
  routes, including CI and maintainer approval gates.
