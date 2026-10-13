# Shallow executor clones

Investigate whether executors can work from local depth-one clones with enforced
history exclusion, receive corrections, and return reviewable commits without
access to the original repository. Resolve the preparation, communication, and
delivery choices before adopting a replacement for linked worktrees.

Current [orchestrator guidance](../../../../../orchestrator.md) requires linked
Git worktrees. They isolate edits but share the source repository's history.
The [preparation target](../../../../../../Makefile) creates a branch from local
`master`, copies caches, and prepares a fresh locked environment with offline
setup. Any adopted replacement must preserve a fresh locked environment,
verified readiness and the existing independent review and delivery gates.
Cache copying and offline reconstruction describe current worktree behavior;
they are not requirements of the proposed manual evaluation preparation.

## Investigations

- **TODO** [Sandbox isolation](sandbox-isolation/README.md): test actual Codex
  read denial, clone preparation, local commits, and isolation across resumed
  sessions; compare custom agents with separately launched executors.
- **TODO** [Artifact delivery](artifact-delivery/README.md): test commit import,
  patch transfer, and orchestrator publication from the clone, including
  separate evidence and cleanup commits and an advanced upstream base.
- **DONE**
  [Orchestrator-prepared evaluation environments](https://github.com/msitarz/ataraxia/blob/c9a24b3f8cccfb9392ec12db2029dfe03887786d/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/environment-preparation/README.md):
  native online preparation, readiness, installed hooks, and bounded denied-
  access controls passed in the tested condition. The report recommends this
  candidate condition-specifically; it does not adopt policy.

Each Investigation owns one recommendation and checked evidence under the
[Investigation rules](../../../../../work-definition.md#investigations).
The relocated
[communication Investigation](../../../../evaluation-sandboxes/executor-communication/README.md)
remains an input to the combined recommendation. Isolation and communication
may prepare independent disposable fixtures; the
integrated delivery demonstration uses their verified configuration and handoff.
Treat a blocked boundary as evidence against a candidate rather than bypassing
it. Combine the reports into one adoption recommendation and identify further
Work; production implementation is outside these Investigations.

## Implementation follow-up

[Managed evaluation sandboxes](../../../../evaluation-sandboxes/README.md)
owns replacement preparation/runtime planning under the approved #315
disposition. The ownership correction awaits review; this tree retains isolation
and artifact-delivery Investigations, the combined recommendation and registry
maintenance.

- **ABORT** Optional shallow executor implementation Work: superseded by managed
  creation, enforcement, execution and relocated import; no active child
  remains. Its [retained contract](implementation/README.md) awaits reviewed
  cleanup; delivered
  [registry usage](implementation/dependency-snapshot/registry-selection.md)
  remains until separate consumer-gated cleanup. Unsatisfied outcomes are not
  DONE.
- **TODO** [Registry selector cleanup](registry-selector-cleanup/README.md):
  independently scoped maintenance leaf; remove obsolete tooling after the
  revised plan merges and consumer/owner-link review permits safe removal.

## Proposed outcome and boundaries

- The historical manual direction used trusted online native Git preparation and
  existing `make setup` / offline `make verify-setup`, with fresh final-location
  environment, caches and pinned hooks. The
  [Work-owned preparation inputs](../../../../evaluation-sandboxes/preparation-input.md)
  preserve manual inputs;
  [managed creation](../../../../evaluation-sandboxes/creation/README.md) owns
  future preparation, exact input, object independence and recovery.
- Managed [enforcement](../../../../evaluation-sandboxes/enforcement/README.md)
  and [execution](../../../../evaluation-sandboxes/execution/README.md) own
  boundaries, actual start and exact-session corrections after readiness.
  [Import](../../../../evaluation-sandboxes/artifact-import/README.md) owns
  accepted commits into a designated full-history Work branch, preserving review
  and
  [evidence-before-cleanup order](../../../../../acceptance-tracing.md#work-delivery-commits).
  Publication remains orchestrator-owned under existing gates.
- For an evaluation that excludes history, declare its frozen base, permitted
  files and references, session freshness, and filesystem and network access.
  Check current-tree reports, answer fixtures, and links for prohibited prior
  evidence; shallow history does not remove them. Prepare fresh sessions without
  inherited answers. Verify the declared restrictions before the run; if they
  cannot be established, report the blocker rather than claim isolation.

A shallow clone removes historical examples from ordinary Git navigation; it
does not prevent reuse of patterns in current code. Removing the remote is a
convenience restriction: an agent with access to the original repository can
still read its history or fetch directly from its path. Describe that exposure
accurately. Evaluations needing enforced exclusion must use an environment
that denies source-repository reads and unauthorized fetch or reference access.
This Work does not build a new sandbox or network-control system.

## Ownership and dependencies

The
[Work-owned preparation inputs](../../../../evaluation-sandboxes/preparation-input.md)
retain transitional manual implementation inputs. Lasting usage is promoted
only when managed commands deliver. Existing Make targets own setup behavior;
[orchestrator guidance](../../../../../orchestrator.md) owns executor handoff
and artifact return. Follow the [WDR workflow](../../../../../wdr-workflow.md)
for any consequential policy adoption; Investigations recommend rather than
approve that policy. Current guidance remains authoritative until adoption.

Follow [empirical evaluation guidance](../../../../../evaluation.md) for
permitted resources, contamination, and verified isolation. This Work
contributes the concrete clone and history-access requirements without creating
a second evaluation owner. Use the
[glossary's Worktree meaning](../../../../../ubiquitous-language.md) so
independent clones are not described as linked worktrees.

## Acceptance

- **AC-1 TODO** The isolation and artifact-delivery Investigations, delivered
  preparation findings and relocated communication findings are integrated with
  inspectable actual evidence, candidate tradeoffs, recommendations, and
  unresolved limits.

  Validation: check `master` for the owned child outcomes and relocated
  communication outcome, then review retained evidence; distinguish documented
  capabilities from tested behavior.
- **AC-2 TODO** The combined recommendation selects or rejects a concrete path
  from isolated handoff through corrections to reviewable publication, preserves
  review and commit gates, and identifies any further implementation Work.
  Validation: trace the proposed flow against the reports, including denied
  source access, unchanged and advanced bases, and failed execution.
- **AC-3 TODO** Lasting findings are promoted to authoritative owners before
  this parent is removed, without presenting recommendations as adopted policy
  or introducing a second evaluation lifecycle.
  Validation: inspect owner links, the parent map, and any follow-up Work or
  WDR against [documentation ownership](../../../../../README.md).

## Execution gate and limits

The completed environment-preparation Investigation supports the native online
candidate only in its tested Darwin Intel deterministic condition; no model
session or filtered-answer condition was tested. The maintainer authorized this
revised planning direction and abandonment of the unrun snapshot subtree, not
implementation or policy adoption. The retained implementation contract records
supersession and ABORT rationale; delivered registry selection and historical
evidence remain intact. The approved #315 reconciliation replaces the
unimplemented manual preparation and runtime contracts with managed owners;
import retains its own gates. Cleanup is independently schedulable after
consumer review; it preserves the active Investigation examples through frozen
source links. Follow the
[planning gates](../../../../../workflow.md#decisions-and-new-splits).

The retained child reports and audit preserve completed bounded probes and
trials, including failed attempts. The managed follow-up is planning only and
changes no current preparation policy. Merge the reviewed ownership correction
before implementation execution. Before any model-backed trial, declare
fixtures, prompts, conditions, selected model and effort, maximum runs and
corrections, a time or token budget, and stop handling; obtain applicable
maintainer approval. Use the existing leaf policy and reassess each delivery
against the
[review target](../../../../../workflow.md#scope-and-sizing).

Do not change model selection, review topology, current-code reuse policy, or
GitHub publication ownership. Use disposable repositories and non-secret
canaries. New sandbox systems, production tooling, comparative performance
trials, and live GitHub publication trials require separate scope and applicable
authorization. Record
limitations without claiming that clone preparation alone prevents history
access or establishes evaluation validity.
