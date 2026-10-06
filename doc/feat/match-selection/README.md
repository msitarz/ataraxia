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

Evaluate the repository's pinned Ruff capabilities against this seed and small
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

  Validation: manually review the recommendation against the preserved seed,
  pinned tool/version evidence and supported capabilities, representative
  positive and negative examples, and the existing engineering/testing guidance;
  run any project-tool experiments through Make and retain their outcomes.
