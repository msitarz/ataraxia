# Accepted executor commit import

Depend on [accepted runtime output](../executor-runtime/README.md).
Own orchestrator-controlled explicit fetch/rebase into a full-history designated
Work branch after independent acceptance and final correction. Use the
[reviewed delivery path](../../artifact-delivery/delivery-protocol.md).
Executor state/auth and permissions remain untouched; master is not a delivery
target. Host production operations retain signing settings and normal hooks.

Keep this leaf within a five-minute review; split before oversized execution.
Automated tests use criterion markers scoped to this README; manual judgments
remain independent review. All criteria are planned, not observed evidence.

## Acceptance

- **AC-1 TODO** Import requires the exact accepted executor tip/base and
  expected Work HEAD, fetches only the explicit assigned ref into a nonshallow
  receiver and rejects stale acceptance, missing ancestry or unexpected refs
  without publication.

  Validation: Criterion-marked local Git tests inspect
  fetch refs, receiver history, accepted identities and compare-and-swap guards;
  independently review acceptance/evidence bindings.
- **AC-2 TODO** Unchanged-base import preserves identity; advanced-base rebase
  preserves authors/order, binary bytes, modes, rename/delete and
  implementation/evidence-before-cleanup boundaries. Conflict halts publication
  until reviewer-owned resolution and evidence refresh.

  Validation: Criterion-marked fixtures cover unchanged, clean advanced and
  conflicting bases plus exact tree/metadata/boundary checks; manual independent
  review accepts refreshed latest-head evidence after rewriting.
- **AC-3 TODO** Only reviewed latest Work-branch output is handed to
  orchestrator publication under usual PR/CI and maintainer gates, without
  master rewrite, source mutation or executor publication access.

  Validation: Criterion-marked local publication/guard tests verify designated
  refs and unchanged source/master; independently review the orchestrator
  handoff. Live GitHub PR/CI experiments, alternate patch transport and
  default-policy adoption are outside scope.
