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
render each fence in a bounded child. Inject a typed process collaborator for
timeout/refusal tests while real backend tests run through the owned checker.
The [rendering owner](rendering/README.md) fixes a Python API worker calling
`mermaidx.render(source, backend="quickjs").svg()`, with our checker CLI owning
process execution/reporting rather than invoking the upstream mermaidx CLI.

Names/module grouping are proposed; ownership, precise records and observable
behavior are required. Resolve final signatures here before downstream delivery
rather than inventing an incompatible interface during Make wiring. Preserve
one authoritative implementation and current strict typing/test guidance.

- **AC-1 TODO** Given accepted extraction, rendering and Make deliveries,
  integrated `doc-check` obeys selected/default path, diagnostic, offline and
  read-only contracts without weakening existing checks.

  Validation: independently review child evidence and run focused Make/backend
  integration tests on the combined revision, plus doc/ac checks.
