# Select Markdown and extract Mermaid fences

After accepted [setup](../../setup/README.md), deliver the discovery/extraction
functions and fence record in the
[checker boundary](../README.md#proposed-public-boundary). The review question
is whether Markdown selection yields only the intended Mermaid source with
correct locations. Rendering/process handling and Make wiring belong to
subsequent Works.

Rumdl is the current Markdown tool; no reusable Python parser has been
established. Choose a suitable parser or focused implementation within this
scope, including a development-only parser dependency and lock update if needed.
Explain that choice and its line mapping; do not promote the investigation's
fixture-only regex to production. Recognize fenced blocks whose first
info-string token is exactly `mermaid`, including backtick and tilde fences,
valid varying lengths/indentation and container nesting. Exclude inline code,
indented code and Mermaid-looking text inside other fences. Honor Markdown
closing/EOF semantics. Preserve source line count while removing Markdown
container/fence indentation so diagram locations map to original lines.
Return empty Mermaid fences for rendering rather than dropping them.

Selectors are file/directory paths under the existing Make convention;
directories recursively select Markdown, duplicate selections check each file
once, and nonexistent inputs fail clearly. No selectors means repository
Markdown, excluding Git/environment/cache directories consistently with
existing documentation selection. Discovery/extraction are read-only and
perform no backend import, rendering or network operation.

- **AC-1 TODO** Given Markdown fence variants above, extraction returns exactly
  the Mermaid fences, including empty fences, with independent expected source,
  fence lines and content lines; unrelated code/text is excluded.

  Validation: criterion-marked public extraction unit tests cover the stated
  cases, including containers and EOF closure. Independently review parser
  choice, line mapping and explicit expected records.
- **AC-2 TODO** Given selected files/directories, duplicates, invalid inputs and
  empty selectors, discovery returns the promised Markdown scope or contextual
  input failure without checkout outputs or backend execution.

  Validation: criterion-marked public discovery tests use disposable files and
  compare complete selected paths/error context. Review default exclusions
  against existing rumdl selection; run affected lint/type/doc/ac checks.

Follow current [testing](../../../../testing.md),
[unit guidance](../../../../testing-unit.md) and
[strict typing](../../../../engineering.md#preserve-type-precision). Static
equality fixtures remain opaque when only compared; do not duplicate their
schema or add runtime validation solely to satisfy typing.
