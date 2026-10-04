# Optional shallow executor tooling

Implement optional Make-owned preparation, executor control and
accepted-artifact import from the
[tested recipe](../sandbox-isolation/successful-recipe.md) and
[delivery evidence](../artifact-delivery/delivery-protocol.md). Those retained
Investigations establish bounded feasibility, not completion of this Work.

Keep the regular worktree target and current linked-worktree policy. Changing
the default or adopting a delivery policy needs separate maintainer direction
and the existing WDR route. This plan adds no executable behavior or trial.

## Child Works and dependencies

- **TODO** [Dependency snapshot](dependency-snapshot/README.md): select and
  freeze safe offline dependency inputs.
- **TODO** [Clone preparation](clone-preparation/README.md): independent shallow
  clone and fresh offline readiness; depends on dependency snapshot.
- **TODO** [Executor runtime](executor-runtime/README.md): restrictive start and
  exact-session correction; depends on prepared clone readiness.
- **TODO** [Artifact import](artifact-import/README.md): accepted output into a
  full-history Work branch; depends on accepted runtime output.

Each leaf aims at one five-minute review. Reassess behavior, tests and
supporting changes before execution; split further before a delivery exceeds
that scope. Merge this parent map before child deliveries. Follow existing
contribution, acceptance, review and publication contracts rather than creating
another lifecycle. Host commits inherit signing settings; never disable
`commit.gpgsign` for production operations. Hermetic disposable fixture identity
and signing are a distinct test condition.

## Acceptance

- **AC-1 TODO** All four leaf outcomes are integrated and their interfaces
  compose from selected snapshot through accepted Work-branch import, while
  existing worktree behavior remains available.

  Validation: criterion-marked deterministic fixtures exercise composed
  snapshot/setup/import interfaces and the unchanged worktree interface.
  Reuse independently reviewed leaf results, including executor-runtime's
  required actual start/exact UUID resume through the new launcher; review
  interface ownership and acceptance bindings. This does not require or imply
  a whole model-backed full-project trial.
- **AC-2 TODO** Usage and supported-platform limits are promoted to their
  authoritative owners without changing default policy or claiming untested
  configurations are supported.

  Validation: independently review Make help, contribution and orchestrator
  guidance against the retained evidence and implementation tests. Normal
  latest-head PR/CI review applies; no live PR/CI experiment is required.
