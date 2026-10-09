# Acceptance tracing

Read when assigning Work acceptance-criterion IDs, recording coverage, or
looking up tests by criterion.

## Criteria and coverage

Give each criterion a stable ID such as `AC-1`, unique within its owning Work
README or spec. The repository-relative path to that file scopes the ID. Write
each criterion as one Markdown list item beginning `- **AC-1 TODO**` or
`- **AC-1 DONE**`, followed by its criterion text. Use the same status labels as
Work maps:

- `TODO` means the criterion's outcome is not yet verified and recorded. This
  includes missing coverage or method declarations, declared methods or
  implemented tests without observed evidence, and failed, skipped, pending, or
  unrun methods.
- `DONE` means an independent reviewer verified the criterion's outcome from
  inspectable evidence. A declared method or implemented test alone is
  insufficient. `DONE` does not itself mean maintainer approval or merge.

## Planned validation and evidence

An indented `Validation:` clause states the planned method for the executor
and reviewer; every manual or other non-test criterion needs one. It is not
coverage, evidence, or proof of completion. Keep it unchanged when marking a
criterion `DONE`. While a criterion remains `TODO`, its plan may change; perform
the revised method before completion.

Inspect evidence where it is produced. Automated behavior needs criterion-
marked tests and selected test execution evidence, following the
[check and evidence policy](validation.md). `ac-check` checks
declarations and references but requires neither a marker nor a `Validation:`
method; passing it does not establish actual test coverage, selected execution,
observed evidence, or review. Measurements and trials use observations in
existing reports or artifacts. Manual judgment requires independent review of
the changed artifact. Apply the [criterion status rules](#criteria-and-coverage)
to these evidence sources.

Complete a criterion when its own `Validation:` method has been performed and
an independent reviewer verified the resulting evidence. Full latest-head CI
is a separate merge gate; it is not a routine precondition for accepting local
behavior evidence. If a criterion or its method explicitly requires a CI
result, keep it `TODO` until that result is observed. Never treat pending CI as
completed evidence or silently waive a CI-specific method to fit the ordinary
publication sequence. Get maintainer steering when that method cannot be
satisfied before cleanup.

## Work delivery commits

1. While the contract exists, run `ac-check`, applicable selected tests, and
   other planned validation methods. Keep failed, skipped, pending, unrun, or
   otherwise unsupported criteria `TODO`.
2. After independent review, commit the implementation and retained contract
   with verified criteria marked `DONE`. Preserve inspectable evidence in its
   source records; do not duplicate manual outcomes beside criteria. Keep this
   verified implementation/evidence commit before the separate cleanup
   commit. Work deliveries with acceptance criteria require both commits and
   must not be squashed.
3. In the cleanup commit, remove the contract and update the parent map. Review
   tests under [test ownership](test-ownership.md) and retain regression tests.

Development fixups may be folded into the verified implementation/evidence
commit; retaining every intermediate commit or SHA is not required. A later
implementation or evidence correction invalidates the affected evidence. Return
its criterion to `TODO`, repeat applicable validation methods, and refresh the
source evidence before marking it `DONE` again. If the contract was removed,
restore it in a corrective evidence commit before making a separate cleanup
commit.

Rebase the completed sequence onto current `master` as linear history while
preserving the verified implementation/evidence commit and the later cleanup
commit in that order. Refresh commit references in their existing evidence
records when a rebase changes the referenced commits. The rebase may replace
commit IDs; it must not combine or discard either required commit.

## Limits

- Declaration checks, tests, and CI establish only the outcomes they verify;
  none establishes a manual or otherwise unrun outcome.
- Any required `TODO` criterion prevents completion. If the Work stops
  unsatisfied,
  follow the abandonment lifecycle in [Work contracts](workflow.md#lifecycle).
- Coverage markers may remain as provenance; Work-targeted commands require the
  owning file. After removal, Git retains the contract and the PR, CI records,
  or linked artifacts retain the evidence.
See [test ownership](test-ownership.md) for removed-probe evidence.

## Pytest markers and lookup

Pytest registers the strict `covers` marker in
[`pyproject.toml`](../pyproject.toml). Use keyword arguments to identify the
owning file and criterion:

```python
@pytest.mark.covers(work="doc/feat/example/README.md", ac="AC-8")
def test_inbound_links(): ...
```

Repeat the decorator when a test covers multiple criteria. Include the covered
criterion text in the test docstring. The checker counts direct `covers`
decorators only on top-level `test_` functions and `test_` methods of top-level
`Test` classes in pytest-style `test_*.py` or `*_test.py` files. It does not
infer collection or count marker assignments, calls inside function bodies,
nested helpers, or decorated helpers.

Acceptance tooling checks and selects tests from both `test/` and `example/`.
The checker statically inspects Python test candidates in those roots, while
the selector passes both roots to pytest and filters by the `covers` marker.
This shared acceptance scope does not change ordinary test discovery:
`make test` remains scoped by pytest's configured `test/` path, and the
dedicated example target continues to run `example/` separately.

## Collecting and running selected tests

Use the Make targets to list or run tests for an owning Work file. `WORK` is
required and must be the repository-relative path to its `README.md` or
`spec.md`. Omitting `AC` selects every marked criterion for that Work; setting
it narrows the selection to one criterion:

```sh
make ac-collect WORK=doc/feat/example/README.md
make ac-collect WORK=doc/feat/example/README.md AC=AC-8
make ac-test WORK=doc/feat/example/README.md AC=AC-8
make ac-check WORK=doc/feat/example/README.md
```

`ac-collect` lists selected tests without running them; `ac-test` runs them.
Both return a nonzero status when no tests match. Criteria verified by manual or
other non-test methods remain documented in the Work and are outside these
test-selection targets. `ac-check` checks declarations for the selected Work
only; see its [evidence limits](#planned-validation-and-evidence). It does not
query CI. Use pytest and existing targeted-test tooling; do not introduce
Gherkin, another runner, or a custom selection plugin.
