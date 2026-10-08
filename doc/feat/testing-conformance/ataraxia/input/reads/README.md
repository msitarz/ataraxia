# Provider reads and exhaustion

Own new `test/ataraxia/unit/test_provider_reads.py` and its strict include. Move
only `test_bar_provider_single_bar`, `test_bar_provider_stop_iteration`,
`test_bar_provider_header_only_exhausts_and_closes`,
`test_bar_provider_skips_blank_rows`, `test_bar_provider_hashable_by_filepath`
and their `file_contents` arrangement from `test_provider.py`. Leave failure
cases/fixtures untouched. Replace mock-open with precisely typed local temporary
CSV arrangements; no new shared conftest/helper dependency.

Preserve decimal conversion to the complete literal Bar: timestamp 1, prices
100/222/93/173, volume 10. Preserve header-only empty output and blank-row input
yielding complete Bars at timestamps 1 and 2 with prices 100/200/50/150, volume
1.

Assert exact StopIteration after the retained single row and real `fd.closed`
after context exit, not a mocked close call or automatic close on exhaustion.
Retain equal-path hash comparison without treating hash values as stable
literals.

- **AC-1 TODO** Given retained disposable CSV inputs and filepath arrangements,
  the real provider yields complete literal Bars, skips blanks, exhausts exactly
  and leaves its actual file closed after context exit with precise test typing.

  Validation: review migrated identities and independent Bars/resource state;
  run the new module and legacy failure remainder, plus the input group's
  checks.
