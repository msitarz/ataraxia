# Function-size guardrails

Add graduated mechanical feedback for function and method size that complements
the approximate 25 executable-line review signal in
[engineering conventions](../../../engineering.md#code-style). Keep this Work
focused on the rule, owner guidance, and lint integration; do not bundle broad
refactors of existing functions. The bounded checker in PR #97 remained one
responsibility but still took substantial effort to understand, motivating an
early size signal.

Read the [Ruff configuration](../../../../pyproject.toml),
[Make targets](../../../../Makefile), and the
[validation policy](../../../validation.md). Official Ruff references:
[PLR0915](https://docs.astral.sh/ruff/rules/too-many-statements/),
[max-statements](https://docs.astral.sh/ruff/settings/#lint_pylint_max-statements),
and [exit codes](https://docs.astral.sh/ruff/linter/#exit-codes).

## Acceptance

- Verify that the repository's pinned Ruff version supports the candidate rule
  and settings. Compare how its measured size classifies representative source,
  script, and test functions, including the acceptance-coverage checker
  introduced in PR #97. Ruff PLR0915 counts statements, not executable lines;
  reconcile that metric with the current engineering guidance before choosing
  it. If the guidance must remain a line-count heuristic, present concrete
  choices to the maintainer before implementation.
- Establish thresholds for the selected metric: at most 25 is within guidance,
  26–50 is advisory, and above 50 is blocking. Align the engineering owner with
  the chosen measure and state that these thresholds guide refactoring rather
  than prescribe function shapes. Prefer Ruff PLR0915; if one Ruff pass cannot
  provide both levels, use a small Make composition with a size-only advisory
  pass and the normal blocking lint pass instead of a custom checker.
- Route both levels through existing Make lint and full CI workflows, including
  targeted paths. Advisory findings must not fail CI; tool, configuration, and
  unrelated lint failures remain blocking. If using Ruff `--exit-zero` for the
  advisory pass, scope it to the size rule only and preserve abnormal tool
  failures.
- Apply the rule consistently to source, scripts, and tests, or justify narrow
  exceptions. Do not add blanket exemptions or split functions only to evade a
  count. Add focused tests for the repository's warning/error integration, not
  tests of Ruff's own rule behavior.
- If existing functions exceed the blocking threshold and their refactors no
  longer fit this Work's review scope, propose small child Works rather than
  broadening this delivery.
