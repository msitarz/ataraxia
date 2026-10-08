# Provider contextual failures

After reads delivery, own all remaining cases/local fixtures in
`test/ataraxia/unit/test_provider.py` and add its strict include: missing/wrong
headers, use outside a context, four malformed row variants, and unterminated
quote. Replace remaining mock-open/source-string plumbing with typed local
temporary CSVs while retaining each input/case identity.

Headers preserve the existing numeric-first-row and `timing` inputs; require
ProviderError with `CSV file must contain a header: <path>` and no cause.
Outside-context use requires `Use provider as context manager` and no cause.
Retain malformed rows for missing/extra columns, non-numeric and empty values:
require contextual `Invalid bar in shard <path>` with each distinctive reason
and ValueError cause. Unterminated quote retains csv.Error cause and parser
reason. Compare contractual message formatting literally while avoiding
incidental upstream wording beyond distinctive reasons. Assert actual opened
file closure after failed context exits; outside-context use must leave `fd`
absent.

- **AC-1 TODO** Given every retained invalid input/context arrangement, the real
  provider raises its precise contextual failure/cause and preserves the
  expected unopened or genuinely closed resource state without caller or
  checkout mutation.

  Validation: review all eight case instances and cause/resource oracles; run
  this module and provider reads, plus the input group's checks. Report newly
  exposed defects for separate repair rather than changing production here.
