# Architecture exploration

Read when exploring, reviewing, or updating architecture; when checking the
maturity of typed boundaries; when retaining a superseded design; or when
converting a reviewed `.pyi` interface into an implementation module.

## Maturity

Architecture has three useful maturity states:

- **Exploratory** types and diagrams are tools for learning. They may be
  incomplete or replaced and do not authorize implementation beyond the
  bounded question.
- **Reviewed** types and diagrams express an agreed boundary and its
  responsibilities. They guide implementation. Change an agreed boundary only
  with explicit reviewed justification, and review the consequential design
  before implementation.
- **Implemented** architecture is supported by code and observed behavior.
  Update the current architectural view to describe implemented behavior and
  label planned or exploratory behavior clearly.

Exploration follows the existing Work gates. When decomposition is unknown,
keep it bounded to the question within the current outcome. If it reveals
independently deliverable outcomes or a material scope change, use the
[whole-tree pause and planning gates](workflow.md#decisions-and-new-splits).
Exploration can resolve uncertainty; it cannot authorize expanded feature
implementation. Consequential design is reviewed before implementation.

## Review a boundary

For an outcome delivered progressively within one Work, an owner may assign a
bounded architecture or typed-wiring review as an intermediate assignment. The
handoff names the artifact and scope, the reviewer, and the stopping point. The
review assignment returns its completed scope and any applicable subordinate
reviews for the owner's review; implementation waits for that review before
continuing. This is an assignment boundary within the Work, not a new Work or a
mandatory phase. The Work's artifact may progress from a contract to reviewed
typed architecture and typed wiring, then completed behavior, with tests
alongside the relevant increment. Use only the increments that fit the outcome.

Review architecture for the outcome it supports. Preserve inherited Work
constraints and make clear:

- The intent and responsibility of each boundary.
- The shared concepts and terms that cross boundaries.
- The invariants each boundary must preserve.
- The direction of dependencies and which layer owns composition.
- The effects a boundary may perform, including I/O and resource lifecycle.
- Which properties are established by static checks and which require runtime
  or delivered-behavior evidence.

Agree on shared boundaries and guarantees. Leave private helpers and incidental
signatures flexible. Refine shared architecture as vertical outcomes are
delivered; do not freeze every module and signature before implementation.

For example, parallel shard processing might use a strategy coordinator that
submits independent shard jobs to workers and collects their results. Keep it
one leaf when the useful outcome is parallel backtesting as a whole. Split out
an isolated worker only when it is independently useful and deliverable. This
illustration does not approve a parallel-shard feature. Later child Works add
behavior without repeating earlier acceptance criteria; regression checks
preserve the behavior already delivered.

## Keep one current view

The relevant current architecture document describes the reviewed current
design and implemented behavior:

- Update the current view when a later outcome changes a shared boundary.
- Distinguish implemented behavior from planned behavior in the current view.
- Retain useful exploratory findings and superseded designs with their status
  and relationship to the current view.
- Prevent retained history from creating a second live definition or an
  interface that shadows the active one.
- Keep retained Works and architecture artifacts through parent completion.
  The maintainer may remove them manually afterward under the
  [Work lifecycle](workflow.md#lifecycle).

Product architecture belongs in [Architecture](architecture.md). Architecture
of repository workflow or development tooling belongs with its workflow or
tooling owner. Use the context whose behavior is being changed.

For `.pyi` conversion, follow
[Engineering's reviewed type-stub rule](engineering.md#reviewed-type-stubs) and
keep the reviewed design traceable without a duplicate active interface.
