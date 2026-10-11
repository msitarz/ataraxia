# Wire fence validation into doc-check

Depend on accepted [setup](../../setup/README.md) and
[rendering](../rendering/README.md). The review question is whether the existing
Make route invokes that boundary once with the promised selection and retains
all existing checks. Do not add a parallel checker command, rename `doc-check`,
alter `doc-format`, weaken rumdl or replace CI defaults.

The existing target already runs rumdl link-graph and formatting checks with
offline/no-sync settings, and `verify-check`/Check CI already reach it. Reuse
that route and the disposable real-tool
[Markdown tests](../../../../../test/make/integration/test_markdown_tools.py)
and their sandbox. Extend them for Mermaid selection/failure and combined
behavior; existing formatting/link/missing-tool tests retain their owners.
No second sandbox or comprehensive revalidation of rumdl is needed.

`ARGS` continues to accept paths under the existing Make convention. Mermaid
inspection uses only those selected files/directories; empty `ARGS` checks all
repository Markdown using the boundary's discovery rules. Preserve rumdl's
existing selected-path plus `.` link-graph check and selected-path formatting
check and their existing fail-fast behavior. Append the checker after those
checks; any reached stage's failure makes the target fail. Mermaid failures
aggregate within the checker. Preserve offline/no-sync
execution and read-only behavior. `verify-check` and existing default Check CI
reach the checker through `doc-check ARGS=`; no new CI job is needed.

Update command help and the authoritative documentation-tool ownership summary
only as needed to describe implemented behavior. Do not require diagrams when
plain prose suffices or claim GitHub/browser rendering equivalence.

- **AC-1 TODO** Given selected paths and an invalid Mermaid fence outside them,
  `make doc-check ARGS=<paths>` limits Mermaid inspection to the selection,
  while preserving existing formatting/local-link graph checks and rumdl
  fail-fast behavior.

  Validation: criterion-marked Make integration tests in disposable checkouts
  exercise real target/boundary behavior, including selected malformed diagrams,
  an excluded malformed diagram and a broken local-link graph. Use shims only
  for routing properties, not backend validity or link-check behavior.
- **AC-2 TODO** Given empty `ARGS` and successful rumdl stages, all repository
  Markdown is checked and multiple diagram failures are reported and fail the
  target; a rumdl failure retains existing fail-fast behavior. Valid
  and no-diagram selections succeed without checkout outputs or network access.

  Validation: criterion-marked Make integration tests run the real prepared
  backend and rumdl with bounded subprocesses and artifact checks offline.
  Independently inspect `verify-check`/Check CI routing and unchanged defaults;
  run default `make doc-check` on the delivery revision.
- **AC-3 TODO** Given the completed wiring, help and documentation identify the
  owned checker and its embedded-rendering limitations without duplicating
  setup contracts or introducing mandatory diagrams.

  Validation: independently review affected documentation ownership and command
  descriptions; run affected doc/ac checks and focused tests under current
  [testing](../../../../testing.md),
  [test ownership](../../../../test-ownership.md) and
  [evidence policy](../../../../validation.md).
