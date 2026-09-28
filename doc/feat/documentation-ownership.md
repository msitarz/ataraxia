# Documentation ownership and routing

Status: in progress

Tracking: [issue #25](https://github.com/msitarz/ataraxia/issues/25).

## Problem and outcome

Current guidance repeats command tables, definitions, review procedures, and
proposed parallel behavior across entry points and detailed documents. ADR 18
mixes worker supervision with a return-type change. Agents load large entry
points and must reconcile copies when making changes.

Deliver the documentation cleanup approved in the maintainer's planning
conversation, preserving runtime behavior, existing contracts, and review gates.
Completion means the owning guidance is in place and verified; this is not
approval of the parallel execution proposal or its implementation.

## Ownership inventory and execution steps

This inventory describes the starting duplication. The resulting ownership map
will live in `doc/documentation.md`.

| Starting duplication | Migration |
| --- | --- |
| Commands in AGENTS and CONTRIBUTING; sample invocation in AGENTS and README | CONTRIBUTING owns development procedure; README owns the runnable example |
| Code, typing, testing, and repair conventions in AGENTS; testing strategy in architecture | Extract engineering guidance |
| ADR procedure and style in AGENTS | Extract ADR guidance and add eligibility and granularity rules |
| Definitions and local parallel contracts mixed in the glossary | Group definitions by responsibility and link to local contracts |
| Workflow gates copied into CONTRIBUTING and parallel planning records | Keep general procedures in the workflow and local evidence in slices |
| Parallel schema, defaults, and lifecycle repeated across README, architecture, ADR, and slice | Keep local contracts in the slice; rationale for supervision in ADR 18 |
| Contribution status and SPDX guidance in several entry points | CONTRIBUTING owns contribution policy; engineering owns source conventions |

Execute in separately committed steps: record this inventory, create owning
guidance, replace AGENTS with routing, reorganize the glossary, compact existing
documents, narrow ADR 18, then verify and record evidence. Fix affected links in
the same step that moves their targets. No new runtime code or architectural
decision is part of this cleanup.

## Acceptance examples

- A documentation task can locate the owner of definitions, procedures,
  contracts, and evidence without reading code conventions.
- A code fix follows engineering and contribution guidance; a feat slice with
  architectural changes additionally follows workflow and ADR routes.
- A new rule updates its existing owner or a document with a distinct reading
  trigger, rather than expanding the entry point or copying a procedure.
- Workflow sessions and status language have a separate glossary section from
  graph runners and executor workers. Local defaults are linked, not defined
  again in glossary entries.
- A return-type change alone does not warrant an ADR. Resource ownership or an
  execution model can warrant one when its architectural impact and motivating
  finding are explained. Each ADR records one qualifying decision; a slice may
  require zero or several.
- ADR 18 remains proposed, covering individual worker supervision. Its removed
  implementation details remain in the parallel specification. Existing accepted
  ADRs and historical approval/validation records retain their meaning.
- Local Markdown links and anchors resolve, required checks pass, and startup
  and representative task reading sizes are recorded against the starting branch.

## Handoff

- Branch: `feat/documentation-ownership`; base for the later PR:
  `feat/parallel_execution`, explicitly requested by the maintainer.
- Defining and executor session: the current Codex conversation. These roles
  share a session; no independent review is claimed.
- Approval: the maintainer reviewed the execution plan and instructed, "then
  execute step by step and commit after each step if there is work to commit."
  The approved scope is recorded above; this instruction authorizes execution
  without another specification gate.
- Stage: executing the approved documentation cleanup. PR creation is deferred
  at the maintainer's request; manual implementation review remains pending.
- Validation evidence: to be recorded below. No unresolved findings yet.

## Validation plan and evidence

Check local links and anchors, ownership and retained requirements, routes for
documentation/code/feat-slice tasks, and the diff for unintended contract changes.
Run `make ci`. Record startup and task reading sizes as word counts, not token
estimates. Subsequent evidence belongs here; the issue links to this record.
