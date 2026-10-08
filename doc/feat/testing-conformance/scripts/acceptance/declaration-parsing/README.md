# Acceptance declaration parsing

Extract only four parser edge cases from legacy `test_acceptance_coverage.py`:
duplicate/malformed/empty criteria, empty/duplicate `Validation:`, outdented
annotations and legacy `Verification:`. Preserve literal criteria/errors and
local Markdown. Own the public checker import/setup for later declaration
leaves. Precisely type/include only this cleaned subset and owned helpers, not
the remaining legacy cases. Call the real parser/checker with temporary files
for path-resolution behavior.

- **AC-1 TODO** Given malformed or noncanonical Work declarations, parsing
  retains only valid criteria and reports the defined errors without treating
  outdented or legacy annotations as methods.

  Validation: review literal parser outcomes and owning-file setup; run marked
  cases, strict typing, lint/format and doc/ac checks.
