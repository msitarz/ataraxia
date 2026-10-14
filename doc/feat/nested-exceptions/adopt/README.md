# Adopt nested exception guidance

Deliver the remaining guidance outcome of the [parent Work](../README.md).
Integrate one bullet or paragraph of at most 90 words into
[engineering conventions](../../../engineering.md#code-style), reviewing the
surrounding section for consistency. Include no code examples, historical links
or tutorial. This is guidance only; no automatic enforcement or production
repairs are authorized.

- **AC-1 DONE** The guidance forbids a handler-bearing `try` lexically nested
  under another handler-bearing `try` anywhere within the same execution scope:
  body, handlers, `else` and `finally`, including through branches and loops.
  It covers `except*` and async equally; allows cleanup when either `try` has no
  handlers, context managers, sequential handlers and separate nested
  function/method scopes; and recommends cohesive helpers that preserve
  operation-specific catches, causes and cleanup/resource ownership rather
  than a helper per line.

  Validation: independently review the complete affected engineering section
  against these forbidden and allowed arrangements, repair boundaries and the
  90-word limit. Confirm the diff changes guidance only. Run `make doc-check`
  and `make ac-check WORK=doc/feat/nested-exceptions/adopt/README.md`.
