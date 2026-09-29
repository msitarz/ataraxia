---
id: F28-03
kind: slice
parent: F28
status: proposed
approved_revision: null
---

# Add documentation checks with honest selection

## Outcome and scope

Deliver the [checker composition and command contract](../design.md#checker-composition)
chosen after slice 02. Add `make docs-check` to `verify-check` so local and CI
evidence use the same non-mutating gates. Keep generic checks in adopted tools
and repository-specific rules in a small typed Python checker.

Choose explicit document-kind schemas. Check IDs, status/stage separation,
required fields/headings, references and ownership routes, ADR number/status
and reciprocal amendment/supersession links. Require frontmatter for newly
enrolled kinds. Preserve historical records through explicit compatibility
profiles; do not require unexplained ADR numbering continuity.

Enforce the [acceptance ID scope contract](../spec.md#acceptance-id-scope) in
`make docs-check`. Resolve namespaces through document-kind metadata and index
definitions by the owning namespace and local ID, not by filename. Static
document-reference checks live here; slice 04 adds collected pytest references
to the same target. Unknown or invalid references fail even for proposed slices;
the requirement for completed test evidence depends on delivery status.

Enforce the [journal entry contract](../spec.md#journal-entries-and-session-identity)
through the same target: owner-scoped event IDs, a YAML mapping immediately after
each entry heading, the six allowed kinds, separate date/role fields, and an
embedded provider/thread identity or explicit unavailable reason. Validate
heading/metadata agreement and kind-specific revision/scope fields. Reject
duplicate keys, unknown fields, aliases, and registration kinds in new entries.
Ordinary journal links belong to the adopted generic Markdown checker; do not
build a session registry or custom journal-reference resolver. Legacy boundaries
and identity associations are explicit appends, not edits to historical entries.
Native history availability is optional local evidence; public CI must work
without private conversation storage.

History checks compare covered approved contracts and append-only journals at
declared revisions. Changes to accepted ADR bodies and completed historical
slices follow their existing amendment policy. Approval-record consistency is
checkable; human authority and understanding remain review responsibilities.

## Proposed iterations

| Step | Concrete artifact and decision | Verification and proposed checkers |
| --- | --- | --- |
| 1 | Pinned generic linter config and a small enrolled doc set; review diagnostics and exclusions | Chosen rumdl rules and fixture probes; `make verify-check` |
| 2 | A first schema/state rule and shared parsing/index seam; review one failing and one clean document | Parser/schema fixtures for entry placement and heading mismatch, duplicate/unknown keys, invalid kinds/dates/roles, embedded provider identity, null-ID reasons, review/approval fields, ordinary YAML examples, invalid owners and tool-failure exit codes |
| 3 | Navigation/reference and ADR reciprocity rules, introduced one coherent rule per review | Acceptance scope resolution, owner-wide event uniqueness across journals, same-number IDs in distinct scopes, dangling/unqualified acceptance references, unreachable required routes and reciprocal records; reuse generic checks for Markdown journal links |
| 4 | Path/directory, staged-index and base-ref selection; review affected-file explanations | Integration fixtures for inbound links, code-only changes, deleted/renamed files, changed config, and an unstaged fix hiding a staged failure |
| 5 | Approval/revision and append-only transition checks; review their limits | Git-history fixtures including a newly created branch-local spec, contract changes after approval, journal correction and explicit legacy-boundary appends, a malformed new entry outside that boundary, and unauthorized body rewrite |
| 6 | Make/CI/hook integration and documentation; review a real failing-to-clean run | Full `make docs-check`, targeted examples, missing required capabilities, history base configuration and `make ci` |

Every row can split into smaller iterations. Extend strict type checking to the
checker code and test meaningful malformed inputs rather than mirror its parser.
Use current integration tests for Makefile behavior where applicable. Defer
caching, automatic fixes, plugin APIs, similarity heuristics, and broad doc/code
drift inference until evidence requires them.

## Acceptance criteria

| ID | Preconditions and action | Observable outcome | Verified by |
| --- | --- | --- | --- |
| AC-1 | Run full checks on clean and malformed enrolled fixtures | Correct kinds, schema, structure and graph rules produce actionable locations; tools leave files unchanged | Unit/integration tests and `make docs-check` |
| AC-2 | Select a path, staged changes or changes since a base | Required related files and global constraints remain checked; staged mode evaluates index contents | Selection and Git-index integration tests |
| AC-3 | Change approved contracts, accepted records or journal history | Applicable transition violations are reported, including new branch-local approved specs; proper amendments/correction appends pass | Git-history fixture tests |
| AC-4 | Remove a required tool/model/base, or run offline | Required checks fail or report incomplete; optional/unavailable transition checks are named and never claimed performed | CLI/integration tests |
| AC-5 | Invoke repository verification and CI | Documentation gates run through the shared target with clear exit codes and compatible hook behavior | Makefile integration tests and `make ci` |
| AC-6 | Define parent and child criteria, move their files, or introduce invalid owners/definitions/references | The scope contract resolves identities consistently; repeated local numbers across scopes pass, while duplicates within a scope and invalid references fail; file moves preserve identity | Namespace and cross-file fixtures, including incremental selection |
| AC-7 | Write entries in the embedded format, resume or start a conversation, split journals, or identify legacy events | Correct entry metadata and repeated native identities pass; malformed placement, duplicate owner-scoped events, invalid kinds/fields and missing approval metadata fail; generic checks validate prose links; explicit unavailable identities and bounded legacy appends pass without private history | Schema, cross-file and Git-history fixtures, generic link-check probes, plus optional local-adapter tests |

## Next review

The [journal](../journal.md) records enrollment, revisions, findings and approvals.
Acceptance-test mapping belongs to slice 04; language integration belongs to
slice 05. Metadata or a successful checker cannot replace manual review.
