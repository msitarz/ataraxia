# Concise acceptance coverage docstrings

Revise acceptance coverage guidance as one bounded documentation delivery.
The proposed rule is that covers markers identify the Work/AC, while test
docstrings concisely describe the actual behavior or slice proved and any
material coverage limit. Verbatim criterion copying is not mandatory; full
criteria remain authoritative in Work contracts and Git after their cleanup.

Update the owning [acceptance tracing](../../acceptance-tracing.md) guidance
and its [testing](../../testing.md) reading route consistently. Reconcile
conflicting active testing-conformance instructions in the
[scripts map](../testing-conformance/scripts/README.md),
[registry map](../testing-conformance/scripts/registry/README.md) and
[acceptance map](../testing-conformance/scripts/acceptance/README.md), checking
for further directly conflicting instructions before delivery. Preserve
coverage identity, accurate partial claims and independent acceptance review.
No checker redesign or broad legacy-test cleanup belongs in this revision.

The maintainer authorized this proposed style for the current registry
observations PR; that local adoption does not complete this guidance revision.

- **AC-1 TODO** Owning acceptance/testing guidance and conflicting active Work
  instructions consistently permit concise behavior/coverage docstrings without
  mandatory verbatim criteria, while preserving marker identity, authoritative
  contracts and truthful material coverage limits.

  Validation: Independently review the affected guidance and reading routes,
  representative complete/partial coverage examples and active instruction
  search. Run doc-format/doc-check and ac-check through Make; confirm no checker
  or unrelated test changes. Keep the complete revision reviewable in five
  minutes and split before expansion.
