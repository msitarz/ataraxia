# Definer guidance

Give an assigned Definer a focused procedural owner and direct discovery route,
analogous to the delivered [Executor guidance](../../../../executor.md).
This Work extracts existing responsibilities; it does not change role authority.

At verified baseline `4d5923ceb209483123f665338599f46d45b8684e`,
[AGENTS.md](../../../../../AGENTS.md) routes executors directly but has no
definer role route. The [glossary](../../../../ubiquitous-language.md) routes
Definer to [orchestrator guidance](../../../../orchestrator.md), whose trigger
is acting as orchestrator. It contains definer authority, handoff reading,
isolation, stopping, and return requirements among coordination instructions.
[Work definition](../../../../work-definition.md) already owns contract content
requirements, but does not own the assigned definer's procedural role.

Add `doc/definer.md` with an acting-as-definer trigger. Move the definer-facing
actions, authority limits, stopping, and return instructions from orchestrator
guidance to that owner, with role-appropriate links to shared policy. Add the
direct AGENTS role route and documentation-ownership and glossary routes.
Replace moved requirements and the handoff's definer-return route with links;
check affected surrounding guidance for duplication and dangling anchors.

Work definition remains the content owner for anyone defining or reviewing a
Work. Workflow, engineering, acceptance, setup, and publication rules remain
at their existing owners. Orchestrator guidance retains role selection,
assignment preparation, model and fresh-session choices, coordination, recovery
decisions, independent review, publisher handoff, and maintainer delivery.
Preserve the delivered executor routes and instructions.

Preserve the full baseline
[definer return contract](https://github.com/msitarz/ataraxia/blob/4d5923ceb209483123f665338599f46d45b8684e/doc/orchestrator.md#definer-returns):
contract revision, outcome, dependencies, risks, unverified criteria, acceptance
evidence, commands run, unrun checks, unresolved criteria, blockers, and
recovered state with evidence applicability after recovery. Preserve completed
and blocked return meanings, assigned-contract and serial parent-map
responsibility, no implementation or recursive delegation, and independent owner
review before acceptance. An extraction gap goes to the owning orchestrator for
steering.

The executor extraction is integrated; no implementation dependency remains.
Complete this guidance before the live trial. The risk is silently losing a
requirement or widening role authority during extraction. This is owner and
route repair under [documentation ownership](../../../../README.md); no new
WDR is planned unless inspection reveals a consequential policy choice.

## Acceptance

- **AC-1 TODO** An agent assigned only the definer role can discover its focused
  owner directly; contract content and shared policy remain at their owners.
  Validation: independently walk AGENTS, documentation ownership, and glossary
  routes; inspect the new owner's trigger and linked policy boundaries, and
  confirm the executor route and instructions are preserved.
- **AC-2 TODO** Extraction preserves existing definer and orchestrator
  responsibilities without duplicated rules.
  Validation: independently compare the baseline orchestrator sections with
  the changed owners and surrounding sections; trace each moved requirement
  and the complete return inventory above, then verify affected links and
  anchors.
- **AC-3 TODO** The guidance supports valid assignments, blockers, completion,
  corrections, and recovery without permitting implementation or self-approval.
  Validation: independently walk a supplied isolated assignment through reading,
  base/setup verification, definition, and completed return; walk an
  inconsistent assignment, out-of-scope finding, unresolved correction, and
  uncertain recovery through stopping and blocked return to owner steering.
  Inspect evidence applicability and independent review before any criterion
  becomes DONE.

These are manual artifact walkthroughs, not live trial execution or proof of
agent behavior. Run `make doc-format`, `make doc-check`, and Work-targeted
`make ac-check`; mechanical success does not establish manual acceptance.
Non-goals: definers implementing the Works they define, new role powers or
policy, mandatory templates or evidence journals, live trials, and unrelated
guidance restructuring.
