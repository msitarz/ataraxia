# Recommendation

Adopt **rumdl 0.2.78** for the next Checker integration Work: one engine for
Markdown formatting, linting, and offline local file/heading-link checks.
The [runtime probe](rumdl.md) passed the key navigation cases. Enable MD051
and MD057 explicitly and define a small formatting policy in `pyproject.toml`.
Frontmatter handling is not frontmatter schema validation.

| Tool | Decision |
| --- | --- |
| [rumdl](rumdl.md) | Adopt for formatting and offline checks |
| [Mado](mado.md) | Defer; documented interface lacks formatting and local-link checks |
| [Lychee](lychee.md) | Reserve for link gaps or separate external-link checks |
| [ASD-STE100 checker](asd-ste100-checker.md) | Defer; registry install failed, source/model setup unverified |
| [stazelabs/ste](ste.md) | Defer; optional prose rules, separate binary/data setup |

## Integration requirements

- Expose check-only `make doc-check` and a separate Markdown-formatting target
  through `make help`. Prepare pinned tools during setup; checks run offline.
- Require agents to use these targets for Markdown formatting and link checks.
  Do not write ad hoc scripts or manually align tables and wrap prose. Agents
  still write content and repair semantic link targets reported by the tool.
- Custom checks may enforce repository-specific contracts, but must delegate
  Markdown formatting and link resolution to the adopted engine.
- Check the full repository for broken incoming links; evaluate selected-file
  execution separately. Probe Mermaid preservation and formatting idempotence
  before a baseline formatting change. Keep external network checks separate.

This Work records evidence and recommendations; dependencies, Makefile targets,
CI, and permanent agent rules are delivered by Checker integration.
