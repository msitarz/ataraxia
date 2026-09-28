# Documentation ownership and routing

Status: validated

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
- Recorded scope: commit `6badaf4`, transcribing the already approved plan;
  base revision: `c15e8f9` on `feat/parallel_execution`.
- Stage: local execution complete; awaiting manual implementation review.
  PR creation remains deferred at the maintainer's request. Commits are local.
- Validation and defining-session review: recorded below. No unresolved findings;
  this review shares the executor session and is not independent.

## Validation plan and evidence

Check local links and anchors, ownership and retained requirements, routes for
documentation/code/feat-slice tasks, and the diff for unintended contract changes.
Run `make ci`. Record startup and task reading sizes as word counts, not token
estimates. Subsequent evidence belongs here; the issue links to this record.

### Completed steps and review

The inventory, ownership extraction, routing, glossary separation, document
compaction, and ADR cleanup were committed separately at `6badaf4`, `554b1a0`,
`7c0462b`, `749f4cb`, `f17b656`, and `6752428`. This final step records verification
and review corrections. The defining session reviewed those commits and the final
verification diff against the approved scope; the final delivered commit is
recorded in issue 25 after committing. Manual review has not occurred.

Ownership review removed remaining literal toolchain/format settings and copied
issue/repair rules in favor of their configuration or guidance owners. Routing
walkthroughs covered a documentation change, a code fix, and a feat slice involving
architecture. Each locates the relevant owner; unrelated routes remain conditional.
Delivery approval gates, precise typing guidance, lifecycle contracts, and branch
base overrides remain discoverable. Historical workflow acceptance criteria and
review evidence retain their original meaning.

Only Markdown changed. Accepted ADRs are byte-for-byte unchanged. The parallel
slice's JSON example and entire acceptance table are unchanged; ADR 18 remains
proposed, and this cleanup authorizes no parallel implementation. Its failure
continuation/output policy still awaits specification review. The existing cloud
plan is retained once in architecture and flagged as needing its own architectural
record before implementation; this cleanup creates no cloud decision.

### Checks

`make ci` passed on 2026-09-28 after the document cleanup and again during final
verification: 142 repository tests, 3 example tests, 97.12% branch-inclusive
coverage, Ruff checks, strict Pyrefly and expected negative cases, Tach checks,
installed-wheel smoke test, and audit of 38 packages. Final local Markdown
links/anchors and whitespace checks passed; commit hooks passed at each completed
step. No required checks were unavailable. The existing build-cache warning did
not fail the build or installed-wheel check.

### Reading sizes

Word counts use whitespace splitting against base revision `c15e8f9`. These are
guidance sizes, excluding task-specific source, tests, feat specifications, and
referenced ADRs. Code and architectural feat rows conservatively count complete
architecture and contribution files, even where routing permits selected sections.
The documentation row includes the engineering repair section only. This slice's
inventory, handoff, and evidence are excluded from shared-guidance counts.

| Reading scope | Before | After |
| --- | ---: | ---: |
| Mandatory startup | 3,167 | 1,031 |
| Documentation change before contribution checks | 3,167 | 1,831 |
| Code task including architecture and contribution guidance | 5,456 | 3,846 |
| Architectural feat slice guidance | 6,838 | 6,446 |

Mandatory startup reading fell by 67.4%; AGENTS alone fell from 2,164 to 233 words.
The architectural feat route still requires substantial context because all its
responsibilities apply. Ownership and single-decision checks require review;
passing CI alone does not prove semantic duplication is absent.
