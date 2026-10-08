# Checker CLI outcomes

Use `test/script/commit_message_support.py` for typed process arrangements. Own
new `test/script/integration/test_commit_message_cli.py` and its strict include.
Move only `test_accept_formatted_or_absent_body` and
`test_reject_unformatted_body` from the legacy module. Retain all 18 acceptance
and seven refusal inputs, adding descriptive parameter IDs, precise annotations,
Given/When/Then phases, and concise slice docstrings/coverage markers.

Preserve empty/comment-only messages, ordinary and unrestricted long subjects,
absent/short/exactly-72-column bodies, bullets/continuations, labeled sections,
standalone long tokens with indentation/list/trailer prefixes, breaking-change
trailers, ignored comments, CRLF, merge/fixup/revert subjects. Preserve missing
separator and over-width plain/bullet/indented/tab/mixed-token refusals.

Invoke the actual checker using `test/script/commit_message_support.py` and
disposable explicit process state. Assert exact 0/1 exits, empty success
output, complete independent
refusal diagnostics where formatting is contractual, and unchanged original
bytes on both outcomes. Expected diagnostic text and message bytes must not come
from calling checker helpers. Leave scissors, Git-hook, and prek cases
untouched; add no checker API changes, properties, or new shared fixture
responsibility.

- **AC-1 DONE** Given every retained formatting input, the real checker CLI
  produces its literal accepted/refused outcome and preserves input bytes,
  including the width boundary and CRLF, under isolated bounded processes.

  Validation: review the old-to-new case inventory and independent oracles; run
  focused migrated cases plus the legacy remainder, strict typing including
  support dependencies, lint/format and doc/ac checks. Report skips/failures;
  require latest-head full CI before merge.
