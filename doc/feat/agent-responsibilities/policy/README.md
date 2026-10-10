# Adopt responsibility-based agent routing

Replace the current Sol-low-for-all-leaves instruction in
[orchestrator guidance](../../../orchestrator.md) with the maintainer-selected
responsibilities below. Aim for one policy question reviewable in about five
minutes, including supporting glossary and WDR edits. If integration exceeds
that target, return a proposed split for plan review before expanding delivery.

| Role | Model and effort | Bounded responsibility |
| --- | --- | --- |
| Definer | GPT-6.1 Sol, medium | Define Work contracts: scope, dependencies, edge cases, architecture fit, acceptance criteria, and validation. |
| Executor | GPT-6 Luna, medium | Implement code, tests, or other bounded changes under approved contracts. |
| Cleaner | GPT-6 Luna, medium | Perform maintainer-confirmed post-merge operations under cleanup guidance. |
| Publisher | GPT-6 Luna, medium | Mechanically publish the exact independently reviewed artifact and description under PR guidance. |

The orchestrator still scopes the overall objective, assigns bounded tasks,
integrates dependencies, independently reviews definitions, artifacts, and
evidence, and owns maintainer handoff and final-CI assessment. The definer owns
the assigned contract changes, including serial coordination of shared parent
maps, but does not implement code or approve its own definitions. The executor
reports contract gaps before expanding scope. Cleaner and publisher gain no
artifact-review or merge authority. Role selection follows responsibility;
do not leave a contradictory default for Investigation or Evaluation leaves.

Keep role/model routing and definition handoffs in orchestrator guidance;
add shared role meanings at the [glossary](../../../ubiquitous-language.md).
Use the Work README and linked owners as the handoff context, adding only
missing steering and delivery identifiers. Definition returns identify the
contract revision, dependencies, risks, and unverified criteria; execution
returns identify the artifact revision and evidence. Publisher handoffs pin
the exact reviewed commit and approved description; cleanup handoffs include
the PR, branch, worktree, reviewed head, and merge IDs. Their role-specific
returns and refusal rules remain at the procedural owners rather than being
copied into general orchestration guidance.

Adoption depends on the delivered
[branch-cleanup procedure](../../../branch-cleanup.md) and
[cleaner route](../../../orchestrator.md#roles-and-delegation), plus merged
[publisher guidance](../../../publisher.md). Those
owners retain cleanup and publication procedures and their orchestrator routes.
Integrate without duplicate procedures or competing model definitions;
coordinate shared guidance, glossary, parent maps, and WDR index edits serially.

Add a WDR for this role/model decision, reconcile the old leaf instruction, and
amend [WDR 13](../../../wdr/0013-use-sol-low-for-all-leaves.md) with reciprocal
metadata and index changes in the adoption PR. WDR 18 records cleanup, and 19
records publisher delegation; coordinate the next unused number, currently 20,
at delivery. Preserve accepted history and the original comparison's
conclusions. Record maintainer judgment and artifact-review rationale without
treating this small planning output as cost evidence or claiming comparative
superiority.

Preserve current orchestrator model selection, Work-tree ownership and topology,
agent-creation authorization, isolated worktrees, consolidated corrections,
independent review, maintainer merge authority, and latest-head full-CI gates.
Frozen empirical protocols retain their declared conditions and authorization
requirements. Add no benchmark, code implementation, acceptance-test policy,
or changes to the separate PR #205 plan.

- **AC-1 TODO** Given adopted cleanup and publisher guidance, current owners
  consistently route the four responsibilities and selected models, distinguish
  contract definition from implementation, and retain concise verifiable
  handoffs, independent review, and existing delivery authority.

  Validation: manually trace definition, implementation, publication, and
  cleanup handoffs through their owners; inspect glossary consistency, WDR
  amendment metadata, prerequisite integration, preserved gates and protocols,
  and the complete diff's five-minute review scope.
