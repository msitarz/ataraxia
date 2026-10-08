# Acceptance declaration parsing

Own four `parse_criteria` edge cases: duplicate/malformed/empty criteria,
empty/duplicate `Validation:`, outdented annotations and legacy
`Verification:`. Preserve independent criteria/errors; keep Markdown local.
Precisely type/include the module and helpers in strict Pyrefly. Call the real
parser or `check_work`, using temporary files for path-resolution behavior.

- **AC-1 TODO** Given malformed or noncanonical Work declarations, parsing
  retains only valid criteria and reports the defined errors without treating
  outdented or legacy annotations as methods.

  Validation: review literal parser outcomes and owning-file setup; run marked
  cases, strict typing, lint/format and doc/ac checks.
