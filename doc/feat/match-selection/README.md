# Match selection investigation

Investigate tooling and guidance for suitable single-value branching. The
transformed seed is `unsafe_case` in
[worktree removal tests](../../../test/make/integration/test_worktree_removal.py).
Its original repeated conditional arrangement was:

```python
if condition == "dirty":
    with (destination / "Makefile").open("a") as stream:
        stream.write("# undelivered\n")
if condition == "untracked":
    (destination / "keep").write_text("undelivered")
if condition == "locked":
    repository.git("worktree", "lock", str(destination))
```

The fixture now uses `match` for those mutually exclusive arrangements,
including an explicit main-worktree case; shared worktree preparation remains
outside selection. This example motivates investigation, not a general rule.

A second seed is `arrange_changed_input` in
[registry selection inputs](../../../test/script/selection_inputs.py). Its
original exclusive chain was:

```python
if change in destinations:
    shutil.copyfile(changed, destinations[change])
elif change == "file":
    (case.cache / "uv/archive-v0/dependency/payload.txt").unlink()
elif change == "link":
    link = case.cache / "uv/wheels-v6/pypi/dependency/1.0-py3-none-any"
    link.unlink()
    link.symlink_to(case.repository)
elif change == "record":
    shutil.copyfile(
        ROOT / "test/script/fixtures/registry_selection/unapproved.json",
        case.record,
    )
else:
    raise ValueError(f"unknown fixture input: {change}")
```

The helper now matches explicit declaration/evidence, file, link and record
cases. The declaration/evidence destination mapping remains shared outside the
match; indexing occurs only in those matching cases, and unmatched input keeps
the same ValueError. Preserve this example for the investigation alongside the
first seed; it records no tooling recommendation or policy.

Evaluate the repository's pinned Ruff capabilities against these seeds and small
counterexamples. Compare supported Ruff options with other linters or a
guidance-only approach. Consider false positives, whether conversion preserves
independent versus exclusive conditions and unmatched-input behavior, and
examples where `if` remains clearer (guards, unrelated predicates, or
overlapping conditions). Do not enable rules or adopt repository-wide policy in
this Work. No investigation result is recorded yet.

- **AC-1 TODO** A reviewable recommendation compares pinned Ruff, alternative
  tooling, and guidance-only options for suitable single-value branching,
  explains safe-conversion limits and false positives with examples, and states
  when `if` is preferable and whether a separate adoption Work is warranted.

  Validation: manually review the recommendation against the preserved seeds,
  pinned tool/version evidence and supported capabilities, representative
  positive and negative examples, and the existing engineering/testing guidance;
  run any project-tool experiments through Make and retain their outcomes.
