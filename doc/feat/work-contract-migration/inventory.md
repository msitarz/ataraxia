# Initial migration inventory

Baseline: `2c92a906c7de1838965ff05a0c4c96c8da4409cd`, before creating this Work.
This is a bounded migration input, not a permanent inventory or completion
record. The [inventory Work](inventory/README.md) owns reviewing completeness
through parent maps and linked contracts before execution.

## Active contracts

Filename discovery found **31 existing Work READMEs** under `doc/feat`:
two new-format references and 29 remaining contracts. No `spec.md`
was found outside environment/cache/Git directories. The new migration tree is
additional and already follows the template.

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

These three files are retained historical/planning inputs; links from current
contracts require review before any content is reclassified as a live
requirement. They are not wholesale contract-rewrite targets:

- [delivery-protocol.md](../evaluation-sandboxes/artifact-import/delivery-protocol.md).
- [isolation-input.md](../evaluation-sandboxes/isolation-input.md).
- [preparation-input.md](../evaluation-sandboxes/preparation-input.md).

## Guidance and routing surfaces

| Owner | Migration concern |
| --- | --- |
| [Template](../../work-contract-template.md) | Authoritative structure and outcome prompts; preserve the reviewed examples. |
| [Work definition](../../work-definition.md) | Fixed-heading/template prohibitions, repeated authoring prompts, long historical examples, and specialized Work requirements. |
| [Acceptance tracing](../../acceptance-tracing.md) | List syntax, Validation clauses, marker lookup/coverage semantics, selection commands; preserve actual evidence, independent review, and delivery commits. |
| [Evidence policy](../../validation.md) | Criterion-specific Validation-plan requirement; preserve local evidence versus CI distinctions. |
| [Definer](../../definer.md), [executor](../../executor.md), [orchestrator](../../orchestrator.md) | References to validation, criterion coverage, acceptance tooling, and authoring/return responsibilities; preserve role and review gates. |
| [Workflow](../../workflow.md), [evaluation](../../evaluation.md), [test ownership](../../test-ownership.md) | Align affected reading routes and evidence language without erasing experiment protocols or retained observations. |
| [Shared glossary](../../ubiquitous-language.md) | Validation currently means a mandatory per-criterion clause; distinguish record validation from outcome evidence. |
| [Documentation ownership](../../README.md), [AGENTS.md](../../../AGENTS.md), [CONTRIBUTING](../../../CONTRIBUTING.md) | Discoverable template/acceptance routes without duplicated instructions. |
| [WDRs](../../wdr/README.md) | Record the consequential change under the decision workflow; preserve accepted history except reciprocal amendment metadata. |
| [Makefile](../../../Makefile) | Retired targets, help, and reminders pointing to changed owners/anchors. |

Engineering/testing/architecture owners and CI are supporting checks for
affected references; they are not invitations to revise unrelated policy. Search
results need contextual review: a reference to validation may mean runtime input
checks, experimental protocol, planned verification, or actual evidence.

## Tooling and tests

- [Makefile](../../../Makefile): ac-collect/ac-test invoke
  [acceptance_tests.py](../../../script/acceptance_tests.py); ac-check invokes
  [acceptance_coverage.py](../../../script/acceptance_coverage.py).
- [acceptance_coverage.py](../../../script/acceptance_coverage.py): list-based
  parser, Validation annotation parser, AST marker scanner, and marker reports.
- [work_paths.py](../../../script/work_paths.py) and
  [test_roots.py](../../../script/test_roots.py): shared helpers whose surviving
  callers must be checked before removal.
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
- Markers name **64 distinct Work paths**, of which **64 no longer
  exist**. Those historical references need removal, not restoration of deleted
  contracts. Other test/docstring AC mentions require contextual review.

## Preservation and execution boundary

The existing validated-core and sandbox-listing contracts are reference
examples, not mandatory rewrite churn. Parent/child statuses, shared owner
serialization, safety guarantees, deferred decisions, protocol conditions, and
evidence provenance survive migration. Test markers and per-AC Validation
boilerplate are retired rather than replaced with mapping tables or routine
evidence journals.

No rewritten Work is implemented, no model or sandbox trial runs, and no
historical observation gains broader validity from this migration. Only
contracts in the new migration tree are created by this planning change.
