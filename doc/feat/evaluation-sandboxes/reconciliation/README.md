# Reconcile preparation and ownership

First resolve the existing manual preparation direction and overlapping
runtime/import contracts against the [managed plan](../README.md). This leaf
changes documentation and planning only. It does not build targets or run
preparation, probes or models, with the maintainer-approved #315 disposition
after #316 merged. Publication of the revised #315 still requires independent
review.

Preserve the [manual implementation input](../preparation-input.md) when
moving the useful procedure to a focused usage owner such as
`doc/evaluation-sandboxes.md`. That owner distinguishes historical manual
preparation from pending managed commands, then receives lasting guidance as
those commands deliver. CONTRIBUTING receives no sandbox section; use its
existing Make discovery route, with direct focused links from Make help,
documentation, orchestrator and evaluation guidance when implemented.

## Acceptance

- **AC-1 DONE** The existing clone-preparation, runtime and import Works and
  #315 have reviewed dispositions consistent with maintainer clarification.
  Uncompleted outcomes retain TODO; one owner controls each future outcome,
  without concurrent duplicate runtime or premature abandonment/completion.

  Validation: independently compare integrated #314, frozen #315 and both
  parent maps; apply the approved #315 disposition, then inspect exact owner,
  dependency and status changes before either overlapping tree executes.
- **AC-2 DONE** Useful manual instructions survive as referenced implementation
  input in the focused owner, with setup, privacy, recovery and evidence limits
  intact and broader documents reduced to appropriate routes.

  Validation: independently compare the focused file with the immutable inputs
  and canonical Make setup/hook declarations; walk affected links, run
  `make doc-format`, `make doc-check` and changed-Work `make ac-check`.
