# Obsolete registry selector cleanup

Remove the unused snapshot selector as one small maintenance outcome after
[the corrected managed plan](../../../../../evaluation-sandboxes/README.md)
merges and consumer review confirms safe removal. Do not remove tooling in the
planning PR. Aim for a five-minute complete review; split or report an
active-consumer gap before expanding scope. No runtime/import dependency is
needed once the consumer gate passes.

Inspection at `1c1ae02` found the production selector's only command route in
`Makefile` (`registry-select` invoking `script/registry_selection.py`), its
[usage owner](../implementation/dependency-snapshot/registry-selection.md),
dedicated `test_registry_*` tests and `test/script/fixtures/registry_selection`
fixtures. No source runtime calls it. Test helpers such as
`selection_inputs.py`, `selection_manifest.py`, `selection_process.py`,
`registry_layout.py`, `registry_transport.py`, `support.py` and `conftest.py`
have additional test consumers; do not treat a filename prefix as proof of
exclusive ownership. Historical `testing-conformance` criterion markers
reference removed contracts and remain provenance, not active dependencies.

Two active Investigation contracts,
[literal selection](../../../../../literal-selection/README.md) and
[match selection](../../../../../match-selection/README.md), link
`test/script/selection_inputs.py` as their seed. Before selector deletion,
update those owner links to reviewed frozen Git/source references preserving
the examples and their original condition. Keep current links valid until then;
do not retain dead production/test dependencies solely for examples or abort or
change the Investigation outcomes. Reinspect consumers at the actual cleanup
revision, preserving shared helpers/tests required by any surviving behavior.

## Acceptance

- **AC-1 TODO** Consumer review establishes that removed selector routes,
  documentation, code and dedicated tests/fixtures have no active consumers;
  shared helpers/tests needed by surviving behavior remain usable, and active
  Investigation examples have reviewed frozen source links before deletion.

  Validation: inspect imports, Make/help routes, links, fixture references and
  active Work criteria at the cleanup revision. Independently review the exact
  removal list and preserved consumers; historical coverage markers alone do
  not block removal. Stop and report any unresolved active consumer.
- **AC-2 TODO** Obsolete registry tooling and its dedicated usage/tests are
  removed together; `make help` no longer advertises `registry-select`, and
  normal setup/worktree preparation plus surviving script/Make consumers retain
  their behavior. Retained historical reports and delivered evidence remain
  discoverable.

  Validation: run focused Make/script tests for surviving affected consumers,
  including the existing worktree-creation tests when its setup boundary is
  affected; verify actual target and test paths before execution.
  Run scoped lint/type/documentation checks for changed surviving files and
  inspect Make help and removed-reference searches. Independent review verifies
  evidence preservation and the absence of unrelated deletions. Do not replace
  deleted-feature tests with assertions that mirror the deletion.
