# Match selection guidance adoption

Propose concise selection guidance in the existing
[engineering code-style section](../../engineering.md#code-style), which
currently has no explicit `match` selection rule. This Work preserves the chosen
direction without adopting policy or starting implementation.

Dependency and evidence: the completed
[Investigation and retained probe](https://github.com/msitarz/ataraxia/blob/0a729e412535ea3accfd17ab3a4b4a81271f4883/doc/feat/match-selection/README.md)
recommend guidance only; pinned Ruff SIM116 suggests dictionaries for
fixed-value returns, and no further tool trial is warranted.

Proposed paragraph: Use `match` when one stable value selects among distinct
cases and only one case should run; preserve required unmatched-input behavior.
Keep independent `if` statements when multiple conditions may apply, and use
guard clauses or simple `if`/`else` when clearer. A dictionary lookup can suit a
pure mapping from keys to fixed values.

Future adoption is limited to one short paragraph of at most 90 words, without
code blocks or Investigation/history links in engineering. Existing
type-precision and finite-domain guidance governs source choices; do not repeat
it or introduce a new prerequisite. Exclude general match lint, checker
dependencies, codebase migration, upstream probes, production examples, and
frameworks.

- **AC-1 TODO** Engineering integrates the proposed selection meaning in its
  existing code-style section within the paragraph limit and scope above.

  Validation: manually read the whole owner and surrounding guidance for
  coherent integration, ownership, brevity, selection limits, unmatched-input
  defaults, independent conditions, guards, and fixed-value dictionary mappings.
  Run `make doc-format`, `make doc-check`, `make format-check`, and
  `make ac-check WORK=doc/feat/match-selection-guidance/README.md`. No tests are
  needed for this prose-only adoption; route any concrete implementation issue
  discovered during review to a separate Work.
