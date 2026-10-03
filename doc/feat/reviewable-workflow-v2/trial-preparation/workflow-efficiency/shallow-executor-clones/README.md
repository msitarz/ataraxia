# Shallow executor clones

Investigate whether executors can work from local depth-one clones with enforced
history exclusion, receive corrections, and return reviewable commits without
access to the original repository. Resolve the preparation, communication, and
delivery choices before adopting a replacement for linked worktrees.

Current [orchestrator guidance](../../../../../orchestrator.md) requires linked
Git worktrees. They isolate edits but share the source repository's history.
The [preparation target](../../../../../../Makefile) creates a branch from local
`master`, copies caches, and prepares a fresh locked environment. Any adopted
replacement must preserve those setup guarantees and the existing independent
review and delivery gates.

## Investigations

- **TODO** [Sandbox isolation](sandbox-isolation/README.md): test actual Codex
  read denial, clone preparation, local commits, and isolation across resumed
  sessions; compare custom agents with separately launched executors.
- **TODO** [Executor communication](executor-communication/README.md): test
  handoff, completion, failure, and same-session corrections through
  `codex exec` and assess whether app-server control is needed.
- **TODO** [Artifact delivery](artifact-delivery/README.md): test commit import,
  patch transfer, and orchestrator publication from the clone, including
  separate evidence and cleanup commits and an advanced upstream base.

Each Investigation owns one recommendation and checked evidence under the
[Investigation rules](../../../../../workflow.md#investigations). Isolation and
communication may prepare independent disposable fixtures; the integrated
delivery demonstration uses their verified configuration and handoff. Treat a
blocked boundary as evidence against a candidate rather than bypassing it.
Combine the reports into one adoption recommendation and identify further Work;
production implementation is outside these Investigations.

## Proposed outcome and boundaries

- A Make-owned preparation target creates an independent shallow clone from the
  local repository, with one selected branch, depth one, and no tags. Use
  `--no-local` or a `file://` URL: plain local-path cloning uses local
  optimizations that ignore `--depth`. Do not borrow objects through alternates
  or reference repositories. See the
  [Git clone manual](https://git-scm.com/docs/git-clone).
- Record and verify the selected base commit before handoff; retain local
  `master` as the default under
  [contribution rules](../../../../../../CONTRIBUTING.md#work-branches-review-and-merge).
  Reject an unexpected base or existing destination without overwriting it.
  Cloning transfers committed state; uncommitted source edits are not inputs.
- Remove the source remote after preparation so routine fetches cannot deepen
  the clone. The executor works on its assigned branch and returns local
  commits and evidence. Compare orchestrator import into a full-history
  repository with review and publication directly from the clone; import is
  a candidate, not a requirement. The orchestrator owns publication in both.
  Preserve the required evidence and cleanup commit order under
  [acceptance tracing](../../../../../acceptance-tracing.md#work-delivery-commits).
- Preserve cache reuse, a fresh virtual environment, locked offline setup,
  environment checking, and recoverable setup failures. Do not share a
  mutable virtual environment or silently fall back to a full-history clone.
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

For any adopted implementation, the Make target and its focused tests own
preparation behavior;
[CONTRIBUTING.md](../../../../../../CONTRIBUTING.md) owns its use and setup;
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

- **AC-1 TODO** All three Investigations are integrated with inspectable actual
  evidence, candidate tradeoffs, recommendations, and unresolved limits.
  Validation: check `master` for the child outcomes and review retained
  evidence; distinguish documented capabilities from tested behavior.
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

This PR adds plans and maps only; it runs no sandbox probes or model-backed
trials and changes no current preparation policy. Merge the reviewed plan before
child execution. Before any model-backed trial, declare fixtures, prompts,
conditions, selected model and effort, maximum runs and corrections, a time or
token budget, and stop handling; obtain applicable maintainer approval. Use the
existing leaf policy and reassess each delivery against the
[review target](../../../../../workflow.md#scope-and-sizing).

Do not change model selection, review topology, current-code reuse policy, or
GitHub publication ownership. Use disposable repositories and non-secret
canaries. New sandbox systems, production tooling, comparative performance
trials, and live GitHub publication trials require separate scope and applicable
authorization. Record
limitations without claiming that clone preparation alone prevents history
access or establishes evaluation validity.
