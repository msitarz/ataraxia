# Close Work contracts on explicit maintainer request

## Purpose

Keep Work contracts available for review until the maintainer requests closure
and replace repeated agent-driven mechanics with deterministic tooling.

## Goals

- Retain requested and descendant contracts until explicitly authorized closure.
- Close selected completed contracts and update references through Make.
- Commit and push mechanical closure changes on the reviewed open PR's branch.
- Keep Git branch/worktree cleanup strictly after maintainer merge.
- Replace cleaner-agent operations with deterministic tooling where applicable.

## Glossary

- **Closure:** explicitly authorized removal of selected completed contracts and
  mechanical updates to their parent maps and dependent links.
- **Git cleanup:** removal of verified merged branches and clean linked
  worktrees.

## Non-Goals

- Accept outcomes, merge implementation PRs, or infer completion from tests
  alone.
- Rewrite arbitrary dependency prose or broaden a Work's approved scope.
- Change ordinary implementation publication, CI, or maintainer review gates.
- Bypass repository protection rules, force a push, or discard undelivered work.

## Mechanisms

- A Make target exposes the closure operation through the existing tool
  interface.
- Git and PR metadata establish the reviewed PR head and exact branch tips.
- Canonical parent/dependency entries identify references the tool can update.
- Existing worktree tools provide guarded removal of clean linked worktrees.

## Visuals

The verified baseline at `b14cc86` retains contracts through merge while closure
tooling is pending; the proposed lifecycle permits explicit closure on the
reviewed open PR:

```mermaid
flowchart LR
    I[Implementation and retained contracts] --> R[Review and corrections]
    R --> A[Maintainer requests selected closure]
    A --> C[Make closes contracts on same PR branch]
    C --> P[Normal push and full final-head CI]
    P --> M[Maintainer merges PR]
    M --> G[Separate verified Git cleanup phase]
```

## Acceptance criteria

### **AC-1 TODO** Contracts remain available through PR review

Current lifecycle and publication guidance retain requested and descendant
contracts until the explicit closure authorization defined by
[lifecycle AC-1](lifecycle/README.md#ac-1-done-one-lifecycle-retains-contracts-until-authorized-closure).
Corrections preserve or restore affected contracts and evidence, and maintainer
acceptance, independent review, and full final-head CI remain merge gates.

### **AC-2 TODO** One command publishes deterministic closure

On an explicitly authorized reviewed open PR, a Make command removes the
selected completed contracts, updates references, commits only mechanical
closure changes, and pushes normally to the same PR branch. The final closure
head must pass full CI before maintainer merge. Closure cannot publish
unreviewed implementation changes, target master directly, or open a separate
closure PR; failures preserve recoverable work without declaring success.

### **AC-3 TODO** Mechanical cleanup no longer requires a cleaner agent

The command owns the verified branch/worktree cleanup operations defined by its
contract in a separate post-merge phase or reinvocation, and current guidance no
longer requires a cleaner agent for those operations. Cleanup requires
verified merged closure provenance and cannot follow merely from pushing closure
to an open PR. It preserves unpublished work; the maintainer owns acceptance and
merge.

## Dependencies

- [Work contract template](../../work-contract-template.md) and
  [Work acceptance](../../acceptance-tracing.md): supply the delivered README
  format, outcome headings, and evidence duties consumed by the closure command.
  The remaining contract migration is independent of this lifecycle change and
  retains existing gates until adoption.

## Children

- **TODO** [Authorized closure lifecycle guidance](lifecycle/README.md): define
  retained contracts, mechanical reference updates, publication authority, and
  the decision.
- **TODO** [Mechanical closure command](command/README.md): deliver the Make
  interface and its guarded Git/reference operations.
- **TODO** [Cleanup adoption](adoption/README.md): retire replaced cleaner
  duties and verify the end-to-end lifecycle and reading routes.

## Links

- [Current acceptance and delivery](../../acceptance-tracing.md): owns the
  sequence being replaced.
- [Current branch cleanup](../../branch-cleanup.md): owns merged-tip and clean
  worktree checks to preserve in the mechanical route.

## Additional context

Revising this contract does not authorize closing any Work. The command
interface, canonical reference rules, and detailed publication authority remain
pending in lifecycle AC-2/AC-3. Existing directory paths are retained. The
migration's policy thinning and this Work's lifecycle change have separate
owners. Shared guidance edits use the delivered authoring/evidence rules and are
coordinated with the migration owner to avoid conflicting rules.
