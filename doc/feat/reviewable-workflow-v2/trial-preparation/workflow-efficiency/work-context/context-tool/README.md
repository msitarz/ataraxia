# Work context tool

Provide a read-only Make tool that gathers bounded context for an orchestrator
or executor from an explicitly selected Work and applicable guidance through
`make work-context`. Read selected files from the identified checkout; do not
fall back to a default checkout. This depends on
[completion routing](../completion-routing/README.md), whose DoD the tool
presents from its owner. The
[Work-context parent](../README.md#works) maps the result. Coordinate shared
guidance-owner edits with
[guidance application](../../guidance-application/README.md),
[handoffs](../../handoffs/README.md), and
[PR evidence](../../pr-evidence/README.md); do not rewrite their contracts.

## Acceptance

- **AC-1 TODO** The Make-owned, read-only command accepts explicit role and
  Work selections, reports checkout path, branch, and revision, and presents
  the selected Work's local contract plus applicable guidance sections with
  source links and the filtered DoD; it reads those files from that checkout.
  Verification: invoke `make work-context` for both roles on a sample Work and
  compare output and source links with files in the identified checkout.
- **AC-2 TODO** Ambiguous task or guidance selection requires explicit
  CLI task selection, requested through an actionable diagnostic; missing or
  invalid Work, unsupported role, or missing guidance source returns nonzero
  with an actionable diagnostic. Gathering is bounded and does not recursively
  load every link, ancestor, sibling, ADR, or glossary entry, and does not
  create a second policy manifest.
  Verification: exercise ambiguous selection and each invalid or missing input;
  confirm actionable nonzero diagnostics, then select explicitly and verify
  excluded linked and neighboring material is absent.
- **AC-3 TODO** The tool does not mutate files or Git state and its selected
  guidance agrees with the existing owners and completion-routing contract.
  Verification: compare status and tracked-file hashes before and after both
  role invocations, then review source references against their owner text.

Future behavior is verified with regression tests marked for applicable criteria
and selected acceptance checks, following
[acceptance tracing](../../../../../../acceptance-tracing.md); observed
invocation examples remain evidence alongside their criteria.
