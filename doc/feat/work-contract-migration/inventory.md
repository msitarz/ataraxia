# Migration scope inventory

Baseline: `2c92a906c7de1838965ff05a0c4c96c8da4409cd`, before creating this Work.
Reviewed against `422a2d6a14078a5468723dc00132bc26d637c4b9`, which includes the
committed migration plan. This is a bounded migration input, not a permanent
inventory or completion record. The [inventory Work](inventory/README.md) owns
this scope assessment; its acceptance remains subject to independent review.

## Active contracts

The pre-migration scope contains **31 Work READMEs**: two new-format references
and 29 remaining contracts, including two planning contracts without ACs.
The migration plan adds 11 Work READMEs, giving **42 current contracts**.

Directory discovery and review of every immediate parent map agree: all 35
non-root contracts have links from their immediate parents, and the seven roots
are the six pre-existing Work roots plus this migration. The five rewrite groups
below cover the 31 pre-existing contracts exactly once; final verification also
covers the migration's own contracts. All current Work-owned Markdown links
resolve to these contracts, this inventory, or the three supporting files
classified below. No additional linked live specification or `spec.md` was
found. Remote historical links remain provenance, not additional active
contracts.

| Contract | Rewrite group | Starting disposition |
| --- | --- | --- |
| [reviewable-workflow-v2/README.md](../reviewable-workflow-v2/README.md) | workflow | Planning contract without ACs |
| [reviewable-workflow-v2/live-trial/README.md](../reviewable-workflow-v2/live-trial/README.md) | workflow | Planning contract without ACs |
| [reviewable-workflow-v2/trial-preparation/README.md](../reviewable-workflow-v2/trial-preparation/README.md) | workflow | Rewrite |
| [reviewable-workflow-v2/trial-preparation/trial-contract/README.md](../reviewable-workflow-v2/trial-preparation/trial-contract/README.md) | workflow | Rewrite |
| [evaluation-sandboxes/README.md](../evaluation-sandboxes/README.md) | sandboxes | Rewrite |
| [evaluation-sandboxes/artifact-import/README.md](../evaluation-sandboxes/artifact-import/README.md) | sandboxes | Rewrite |
| [evaluation-sandboxes/enforcement/README.md](../evaluation-sandboxes/enforcement/README.md) | sandboxes | Rewrite |
| [evaluation-sandboxes/execution/README.md](../evaluation-sandboxes/execution/README.md) | sandboxes | Rewrite |
| [evaluation-sandboxes/executor-communication/README.md](../evaluation-sandboxes/executor-communication/README.md) | sandboxes | Rewrite |
| [evaluation-sandboxes/lifecycle/README.md](../evaluation-sandboxes/lifecycle/README.md) | sandboxes | Rewrite |
| [evaluation-sandboxes/lifecycle/active-state-exclusion/README.md](../evaluation-sandboxes/lifecycle/active-state-exclusion/README.md) | sandboxes | Rewrite |
| [evaluation-sandboxes/lifecycle/active-state-exclusion/cleanup-disposition/README.md](../evaluation-sandboxes/lifecycle/active-state-exclusion/cleanup-disposition/README.md) | sandboxes | Rewrite |
| [evaluation-sandboxes/lifecycle/active-state-exclusion/execution-recovery/README.md](../evaluation-sandboxes/lifecycle/active-state-exclusion/execution-recovery/README.md) | sandboxes | Rewrite |
| [evaluation-sandboxes/lifecycle/active-state-exclusion/lock-and-marker/README.md](../evaluation-sandboxes/lifecycle/active-state-exclusion/lock-and-marker/README.md) | sandboxes | Rewrite |
| [evaluation-sandboxes/lifecycle/listing/README.md](../evaluation-sandboxes/lifecycle/listing/README.md) | sandboxes | New-format reference |
| [evaluation-sandboxes/lifecycle/removal/README.md](../evaluation-sandboxes/lifecycle/removal/README.md) | sandboxes | Rewrite |
| [evaluation-sandboxes/reporting/README.md](../evaluation-sandboxes/reporting/README.md) | sandboxes | Rewrite |
| [evaluation-sandboxes/statistics/README.md](../evaluation-sandboxes/statistics/README.md) | sandboxes | Rewrite |
| [package-readmes/README.md](../package-readmes/README.md) | package-readmes | Rewrite |
| [package-readmes/examples-navigation/README.md](../package-readmes/examples-navigation/README.md) | package-readmes | Rewrite |
| [package-readmes/guidance/README.md](../package-readmes/guidance/README.md) | package-readmes | Rewrite |
| [package-readmes/make-tests/README.md](../package-readmes/make-tests/README.md) | package-readmes | Rewrite |
| [package-readmes/product/README.md](../package-readmes/product/README.md) | package-readmes | Rewrite |
| [package-readmes/product-tests/README.md](../package-readmes/product-tests/README.md) | package-readmes | Rewrite |
| [package-readmes/script-tests/README.md](../package-readmes/script-tests/README.md) | package-readmes | Rewrite |
| [package-readmes/scripts/README.md](../package-readmes/scripts/README.md) | package-readmes | Rewrite |
| [conditional-complexity/README.md](../conditional-complexity/README.md) | conditional-complexity | Rewrite |
| [conditional-complexity/adopt/README.md](../conditional-complexity/adopt/README.md) | conditional-complexity | Rewrite |
| [conditional-complexity/investigate/README.md](../conditional-complexity/investigate/README.md) | conditional-complexity | Rewrite |
| [algebraic-data-types/README.md](../algebraic-data-types/README.md) | standalone | Rewrite |
| [validated-core/README.md](../validated-core/README.md) | standalone | New-format reference |

The workflow overview and live trial have no AC declarations. Their rewrite must
preserve the existing planning responsibility for further definition, without
inventing execution thresholds or treating trial planning as completed.

## Supporting sandbox files

These are supporting inputs rather than additional Work READMEs. Their
classification is based on their content and current consumers:

| File | Classification and migration disposition |
| --- | --- |
| [preparation-input.md](../evaluation-sandboxes/preparation-input.md) | Mixed transitional design input and historical provenance, consumed by enforcement and communication contracts. Preserve its native preparation, configuration sanitization, boundary/handoff requirements, and supported-condition limits through those consumers. Its introductory claim that no managed commands exist predates delivered creation: keep that distinction clear in rewritten consumers rather than adopt it as current status. Do not wholesale rewrite the historical procedure or authorize its execution. |
| [isolation-input.md](../evaluation-sandboxes/isolation-input.md) | Historical observations and explicit unestablished capabilities, linked by enforcement, execution, communication, import, and workflow preparation. Preserve frozen conditions, failures, confounds, and limits; no new readiness or authorization follows. |
| [delivery-protocol.md](../evaluation-sandboxes/artifact-import/delivery-protocol.md) | Historical deterministic import protocol, initial failure, recovery observations, and bounded recommendation. Current import requirements belong to the import README. Historical AC-1/AC-2/AC-3 references and old procedure links describe the retired Investigation, not current completion or current criterion numbering. Preserve them as history. |

## Cross-contract requirements and references

| Surface | Rewrite responsibility |
| --- | --- |
| Sandbox parent's `#shared-root-and-ownership` | Preserve the shared contract and update incoming links from execution, lifecycle, active-state, listing, and removal if its heading moves. |
| Sandbox parent's `#children-and-gates` | Enforcement, execution, and statistics consume this ownership/map section. Preserve their prerequisites when maps become Children/Dependencies sections. |
| Execution recovery's `#binding-and-attempts` | Cleanup disposition links to the attempt/binding protocol. Keep the protocol discoverable after headings change. |
| Workflow preparation's `#works` | Trial-contract definition depends on delivered completion/handoff outcomes. Update the link when the map becomes Children without losing those prerequisites. |
| Active-state parent's final Validation paragraph | It maps original leaf AC-1/AC-3 to lock-and-marker AC-1 through AC-3, AC-2 to lock-and-marker AC-2/AC-3 and execution-recovery AC-2, and AC-4 to execution-recovery AC-1 and cleanup-disposition AC-1/AC-2. The original leaf labels are historical, while the child IDs refer to live criteria. Preserve the responsibilities, updating live references or replacing the mapping with outcome links when children are split. |
| Workflow live-trial and trial-contract READMEs | Declaration-check requirements must agree with the final ac-check decision. Missing trial measurements and the parallel-feature contract remain owned by existing trial planning; migration must not invent values or authorize trial execution. |
| Package documentation parent and seven children | Preserve the seven-child sequence, shared README serialization, and planning-before-package-edit gates. Replace generic doc/ac/CI instruction repetition with links to current owners. |
| Validated-core, complexity adoption, and ADT Investigation | Validated-core must integrate before complexity adoption edits engineering. Complexity/ADT investigations may proceed independently; their rewrite must not introduce a merge prerequisite or imply adoption from a recommendation. |
| Execution, reporting, import, and lifecycle consumers | Enforcement and shared active-state delivery precede execution; accepted execution output precedes import; reporting consumes statistics findings and retained execution data. Preserve local recovery and reviewed-disposition prerequisites. |

All local Work links and immediate child-map links resolve at the reviewed
revision. DONE/ABORT map entries describe delivered or abandoned history, not
missing contracts to recreate. Declaration-like examples in the template,
documentation, or test data are not active contracts.

## Guidance and routing surfaces

| Owner | Migration concern |
| --- | --- |
| [Template](../../work-contract-template.md) | Authoritative structure and outcome prompts; preserve the reviewed examples. |
| [Work definition](../../work-definition.md) | Fixed-heading/template prohibitions, repeated authoring prompts, long historical examples, and specialized Work requirements. |
| [Acceptance tracing](../../acceptance-tracing.md) | List syntax, Validation clauses, marker lookup/coverage semantics, selection commands; preserve actual evidence, independent review, and delivery commits. |
| [Evidence policy](../../validation.md) | Criterion-specific Validation-plan requirement; preserve local evidence versus CI distinctions. |
| [Definer](../../definer.md), [executor](../../executor.md), [orchestrator](../../orchestrator.md) | References to validation, criterion coverage, acceptance tooling, and authoring/return responsibilities; preserve role and review gates. |
| [Workflow](../../workflow.md), [evaluation](../../evaluation.md), [test ownership](../../test-ownership.md) | Align affected reading routes and evidence language without erasing experiment protocols or retained observations. Evaluation's no-mandatory-template wording needs context when its protocol uses the new contract. |
| [Testing](../../testing.md), [acceptance tests](../../testing-acceptance.md) | Testing startup routes and the Shape a test marker/docstring rule reference acceptance tracing; acceptance test guidance routes Work criteria to markers. Remove marker obligations while retaining useful behavior descriptions and the distinction between test type and Work completion. |
| [Shared glossary](../../ubiquitous-language.md) | Validation currently means a mandatory per-criterion clause; distinguish record validation from outcome evidence. |
| [Documentation ownership](../../README.md), [AGENTS.md](../../../AGENTS.md), [CONTRIBUTING](../../../CONTRIBUTING.md) | Discoverable template/acceptance routes without duplicated instructions. |
| [WDRs](../../wdr/README.md) | Record the consequential change under the decision workflow; preserve accepted history except reciprocal amendment metadata. |
| [Makefile](../../../Makefile) | Retired targets, help, and reminders pointing to changed owners/anchors. |

Engineering, architecture, PR/publisher, branch-cleanup, and contributor owners
were checked for affected references; they link to current policy or supply
surrounding constraints rather than define a separate marker format. Their
links require repair only if guidance headings move. The existing testing
marker rules above are direct migration edits. These owners are not invitations
to revise unrelated policy. Search
results need contextual review: a reference to validation may mean runtime input
checks, experimental protocol, planned verification, or actual evidence.

## Tooling and tests

- [Makefile](../../../Makefile): ac-collect/ac-test invoke
  [acceptance_tests.py](../../../script/acceptance_tests.py); ac-check invokes
  [acceptance_coverage.py](../../../script/acceptance_coverage.py).
- [acceptance_coverage.py](../../../script/acceptance_coverage.py): list-based
  parser, Validation annotation parser, AST marker scanner, and marker reports.
- [work_paths.py](../../../script/work_paths.py) is imported by the checker,
  selector, and its dedicated unit tests. Retain it for a surviving checker or
  remove it with that surface if ac-check is retired.
- [test_roots.py](../../../script/test_roots.py) is imported only by the checker
  marker scanner and selector. It has no unrelated production caller and can
  leave with those features. Test fixture copying also names both helpers.
- [pyproject.toml](../../../pyproject.toml): strict pytest covers registration.
- [Script acceptance helpers](../../../test/script/acceptance_support.py),
  [Make acceptance helpers](../../../test/make/acceptance_support.py), dedicated
  `test_acceptance_*.py` modules under script unit and Make integration suites,
  and acceptance/selection/declaration fixtures: adapt declaration-only cases
  if retained; remove cases solely proving retired marker/selector behavior.
- [Work path tests](../../../test/script/unit/test_work_paths.py): retain
  relevant path safety for surviving callers.
- AST inspection found **256 covers calls across 63 Python files**
  in `test/` and `example/`, including fixture calls. These are syntax counts,
  not test collection or coverage measurements. Decorators are removed while
  unrelated regression assertions remain.
- All Work arguments in these AST calls are literal strings. They name **64
  distinct absent paths**: **59 `doc/feat/` paths to retired Works** and **five
  synthetic fixture paths** (`doc/example/README.md`, `doc/other/README.md`,
  `test/declarations/README.md`, `test/selection/README.md`, `other/README.md`).
  No decorator refers to a current Work. Synthetic fixture paths are test data,
  not deleted contracts. Remove historical decorators without restoring old
  contracts or transferring obsolete IDs to new criteria.
- Marker calls occur in product unit/integration/acceptance suites, script
  unit/integration suites, Make integration suites, and Python fixtures; no
  calls occur in `example/`. Some fixtures intentionally contain unsupported or
  nested marker shapes. The syntax total does not establish valid collected
  decorators. Selector/parser expected-output strings and AC-bearing docstrings
  also need contextual cleanup, rather than blanket removal of test
  descriptions.

### Dedicated command tests and fixtures

| Surface | Migration disposition |
| --- | --- |
| [Declaration parsing](../../../test/script/unit/test_acceptance_declaration_parsing.py), [declaration reports](../../../test/script/unit/test_acceptance_declaration_reports.py), [Make declarations](../../../test/make/integration/test_acceptance_declarations.py) | Keep meaningful declaration/path cases only if ac-check survives, rewrite them for heading syntax, and retire Validation/marker expectations. |
| [Marker discovery](../../../test/script/unit/test_acceptance_marker_discovery.py) | Retire AST marker-scanning tests with that feature. |
| [Command construction](../../../test/script/unit/test_acceptance_command_construction.py), [command summaries](../../../test/script/unit/test_acceptance_command_summaries.py), [Make selection](../../../test/make/integration/test_acceptance_selection.py) | Retire tests solely exercising ac-collect/ac-test, marker filtering, or empty selections. |
| [Work paths](../../../test/script/unit/test_work_paths.py) | Preserve supported path safety if the checker/helper remains. |
| [Make guidance reminders](../../../test/make/integration/test_guidance_reminders.py) | Update hard-coded ac-check/ac-test command expectations alongside target/reminder changes; retain unrelated reminder and test-routing coverage. |
| `test/script/fixtures/acceptance_markers_*.py`, `acceptance_report_marker_source.py` | Five marker scanner/report fixture files; remove with their retired consumers or replace only data needed by a surviving declaration checker. |
| `test/make/fixtures/declaration_{test,example}_root.py`, `selection_{test,example}_root.py` | Four executable fixture files used by declaration/selection tests; selection-only and marker-execution witnesses become obsolete. |
| Script and Make `acceptance_support.py` helpers | Import/copy retired scripts and shared modules. Reduce to surviving consumers or remove; do not leave stale imports or fixture copy lists. |

### CI and ordinary test routes

[CI](../../../.github/workflows/ci.yml) invokes ci-check, ci-test, ci-examples,
and ci-package. The current Make recipes do not run ac-check/ac-collect/ac-test
as standalone CI gates; these commands are exercised inside tests. Removing
selection must not remove the ordinary example scope or product/script/Make
regressions. The four CI gates and ordinary focused test selection remain.

### Guidance history and remaining decisions

[WDR 6](../../wdr/0006-keep-delivery-evidence-in-prs-and-git.md),
[WDR 9](../../wdr/0009-require-verified-work-completion.md),
[WDR 11](../../wdr/0011-keep-verification-plans-distinct-from-results.md),
[WDR 14](../../wdr/0014-remove-mandatory-pr-records-for-manual-judgment.md),
[WDR 15](../../wdr/0015-use-ci-results-as-evidence-of-mechanical-checks.md), and
[WDR 21](../../wdr/0021-publish-after-local-work-acceptance.md) preserve the
evidence-policy rationale. Their old Verification/Validation language remains
historical; the guidance child owns the new decision and required reciprocal
amendment links. It must preserve observed evidence, independent review, and
verification-before-cleanup boundaries.

The active-state parent still cites the removed five-level recommendation.
The sandbox rewrite owns removing this stale claim while preserving the actual
planning and scope gates. This is a contract conflict, not an unresolved depth
policy decision.

The only planned tooling choice is whether a declaration-only ac-check earns
retention; the tooling child already owns both allowed outcomes and the guidance
child owns coordinated references. No additional unassigned contract or
migration scope blocker was found. Later implementation findings still follow
their owning Work's scope rules.

## Preservation and execution boundary

The existing validated-core and sandbox-listing contracts are reference
examples, not mandatory rewrite churn. Parent/child statuses, shared owner
serialization, safety guarantees, deferred decisions, protocol conditions, and
evidence provenance survive migration. Test markers and per-AC Validation
boilerplate are retired rather than replaced with mapping tables or routine
evidence journals.

No rewritten Work is implemented, no model or sandbox trial runs, and no
historical observation gains broader validity from this migration. The inventory
step changes this scope document only; guidance, tooling, and contract rewrites
remain subsequent Works.
