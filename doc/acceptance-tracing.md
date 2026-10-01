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
  implemented tests without observed results, and failed, skipped, pending, or
  unrun verification.
- `DONE` means the criterion's outcome has been verified and the evidence is
  recorded; a declared method or implemented test alone is insufficient. A
  `DONE` status does not mean review approved or merge is authorized.

## Work delivery commits

1. Verify every criterion while its Work README or spec still exists. Run
   applicable declaration and selected-test checks before removal, as well as
   required manual or other verification. Keep unverified outcomes `TODO`.
2. Record each result beside its criterion. Every active manual or other
   non-test criterion must have an indented `Verification: <specific method>`;
   when complete, add the observed result there. Mark a criterion `DONE` only
   after its outcome and evidence are recorded.
3. Commit implementation and verification with the contract retained and all
   completed criteria recorded as `DONE`. A delivery PR for a Work with
   acceptance criteria has at least two commits: one or more
   implementation/verification commits, then the final removal commit.
4. In the separate final commit, remove the contract and update the parent map.
   Review tests under [test ownership](test-ownership.md) and retain regression
   tests.

A later correction to implementation or evidence invalidates the affected
result. Rerun applicable checks and refresh its `TODO` status, verification
method, and result before removal. If the contract was already removed, restore
it in a corrective evidence commit, then make a separate final removal commit.

## Limits

- Declaration checks, tests, and CI establish only the outcomes they verify;
  none establishes a manual or otherwise unrun result.
- Any required `TODO` criterion prevents completion. If the Work stops
  unsatisfied,
  follow the abandonment lifecycle in [Work contracts](workflow.md#lifecycle).
- `covers` markers may remain after removal for test provenance; Work-targeted
  acceptance commands require the owning file. Use Git history to review the
  retained contract and recorded results.
- Preserve the implementation/evidence and removal commits when merging; do
  not squash this delivery class.

If a temporary probe is removed while its criterion remains active, retain its
one-time method and delivery PR link beside the criterion as described in
[test ownership](test-ownership.md).

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
Both return a nonzero status when no tests match. Criteria verified by manual
or other non-test methods remain documented in the Work and are outside these
test-selection targets. `ac-check` validates their declarations but does not
run the method. It checks declarations for the selected Work only and does not
execute tests or query CI. Use pytest and existing targeted-test tooling; do
not introduce Gherkin, another runner, or a custom selection plugin.
