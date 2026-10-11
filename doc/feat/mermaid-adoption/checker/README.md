# Integrate the Markdown Mermaid checker

Depend on accepted [setup](../setup/README.md); no checker implementation starts
until both required setup targets and offline execution are verified. Deliver
one repository tooling boundary, outside `src/ataraxia`, then its Make wiring.

## Delivery map

- **TODO** [Markdown selection and extraction](extraction/README.md): select
  Markdown and return Mermaid fences with original source locations.
- **TODO** [Rendering and reporting](rendering/README.md): after extraction is
  accepted, force bounded SVG rendering and return contextual failures.
- **TODO** [Make integration](make/README.md): after rendering is accepted,
  use it once from the existing read-only `doc-check` route.

These ordered leaves each target about five-minute review including tests.
Each leaf owns its behavior; the next consumes its accepted public boundary.
Sequence shared Make/test helpers and parent-map edits. Further responsibility
or excessive review effort requires a revised reviewed plan before expansion.

## Proposed public boundary

The prepared mermaidx API already supplies lazy SVG rendering, and
`markdown-it-py` is already locked transitively through Rich. Neither provides
our selected Markdown/source-location boundary or aggregate diagnostics.
Promote the parser to a direct dev dependency in extraction; adapt its tokens
and the accepted rendering API rather than implementing either upstream engine.
Existing `doc-check` already owns offline/no-sync execution and rumdl checks;
the Make leaf only appends the checker and extends existing boundary tests.

Keep this repository tooling under `script/`, outside the trading package.
Extraction owns a frozen `MermaidFence` record: `path: Path`, `fence_line: int`,
`content_line: int`, `source: str`; source lines are one-based. It exposes
`discover_markdown(root: Path, selectors: Sequence[Path]) -> tuple[Path, ...]`
and `extract_fences(path: Path, text: str) -> tuple[MermaidFence, ...]`.
Selection/input failures carry path and reason in a contextual exception.
The [extraction owner](extraction/README.md) fixes `markdown-it-py` CommonMark
parsing with fence-token content/source maps and a direct dev-only locked
dependency.

Rendering owns `check_markdown(root: Path, selectors: Sequence[Path])` and its
CLI entry point. Its typed result holds an exit code `Literal[0, 1, 2]` and
diagnostics; each diagnostic holds path, fence line, optional mapped Markdown
line, category `Literal["input", "setup", "syntax", "render"]` and reason.
Input/setup errors need no fence line. Compose discovery/extraction once and
render each fence in a bounded child. Use ordinary subprocess facilities and
the existing test-helper patterns for timeout/refusal tests; introduce a narrow
typed collaborator only where needed to exercise that external boundary.
The [rendering owner](rendering/README.md) fixes a Python API worker calling
`mermaidx.render(source, backend="quickjs").svg()`, with our checker CLI owning
process execution/reporting rather than invoking the upstream mermaidx CLI.

Names/module grouping and record layout are provisional; retain precise types,
source locations and observable behavior without a process framework or
duplicated diagnostic models. Extraction settles its public interface before
rendering consumes it, and rendering settles its interface before Make wiring.
Preserve one authoritative implementation and current strict typing/test
guidance.

- **AC-1 TODO** Given accepted extraction, rendering and Make deliveries,
  integrated `doc-check` obeys selected/default path, diagnostic, offline and
  read-only contracts without weakening existing checks.

  Validation: independently review child evidence and run focused Make/backend
  integration tests on the combined revision, plus doc/ac checks.
