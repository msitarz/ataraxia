# Select Markdown and extract Mermaid fences

Using the accepted [setup outcome](../../README.md#delivery-map), deliver the
discovery/extraction functions and fence record in the
[checker boundary](../README.md#proposed-public-boundary). The review question
is whether Markdown selection yields only the intended Mermaid source with
correct locations. Rendering/process handling and Make wiring belong to
subsequent Works.

`markdown-it-py` is already present in `uv.lock` through Rich; no production
extractor exists. The acceptance tool's small fence-skipping regex omits
container/source-map semantics and does not fulfill this boundary.
Use `markdown-it-py` with `MarkdownIt("commonmark").parse(text)`, adapting its
`fence` tokens into the owned fence record. Declare it as a direct,
development-only locked dependency rather than relying on a transitive install.
The [usage guide](https://markdown-it-py.readthedocs.io/en/latest/using.html)
describes CommonMark parsing and its token stream; the
[token API](https://markdown-it-py.readthedocs.io/en/latest/api/markdown_it.token.html)
defines `info`, `content` and source `map`. Use token content as diagram source
and convert zero-based map starts to one-based fence/content lines. Do not
promote the investigation's fixture-only regex to production or render Markdown
to HTML. Recognize fenced blocks whose first
info-string token is exactly `mermaid`, including backtick and tilde fences,
valid varying lengths/indentation and container nesting. Exclude inline code,
indented code and Mermaid-looking text inside other fences. Honor Markdown
closing/EOF semantics. Preserve source line count while removing Markdown
container/fence indentation so diagram locations map to original lines.
Return empty Mermaid fences for rendering rather than dropping them.

Selectors are file/directory paths under the existing Make convention;
directories recursively select Markdown, duplicate selections check each file
once, and nonexistent inputs fail clearly. No selectors means repository
Markdown, honoring the existing rumdl exclusions and gitignore selection policy
from `pyproject.toml`; reuse that configuration rather than another maintained
exclusion list. Discovery/extraction are read-only and
perform no backend import, rendering or network operation.

- **AC-1 TODO** Given Markdown fence variants above, extraction returns exactly
  the Mermaid fences, including empty fences, with independent expected source,
  fence lines and content lines; unrelated code/text is excluded.

  Validation: criterion-marked public extraction unit tests cover the stated
  cases, including containers and EOF closure. Independently review the parser
  adapter, line mapping and explicit expected records; do not exhaustively
  revalidate upstream CommonMark parsing.
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
