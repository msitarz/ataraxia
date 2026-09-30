# rumdl

## Pros

- Official docs describe `rumdl check`, `rumdl fmt`, GFM support, TOML
  configuration, and `[tool.rumdl]` in `pyproject.toml`. This fits the existing
  uv/Python toolchain and avoids an ad hoc Python checker.
- MD051 validates link fragments against generated heading IDs. A temporary CLI
  fixture confirmed relative links, duplicate-heading `-1` anchors, YAML
  frontmatter, and ignored inline/fenced code links.

## Cons

- The formatter changes prose whitespace, so formatter policy and rule selection
  need review separately from link checking. No repository-wide baseline
  formatting sweep was run.
- MD051 establishes heading-fragment checks, but adopting it still requires
  deciding the repository's supported link edge cases and pinned configuration.

## Probe / Evidence

- Repo uses Python `>=3.14`, uv `0.12.19`, and `pyproject.toml`. Tested isolated
  tool version: `rumdl 0.2.78`.
- Installed with
  `UV_CACHE_DIR=/tmp/rumdl-uv-cache uv tool run --isolated --from rumdl rumdl
  --version`. Probe:
  `UV_CACHE_DIR=/tmp/rumdl-uv-cache uv tool run --isolated --from rumdl rumdl
  check /tmp/rumdl-probe/docs`; a `target.md#repeat-1` link passed for duplicate
  headings, `#missing` failed, frontmatter passed, and fake links in code
  span/fence were ignored. Formatter probe
  `rumdl fmt --diff /tmp/rumdl-probe/docs/format.md` showed prose whitespace
  rewriting. In `/tmp/rumdl-probe`, `rumdl config file` and
  `rumdl config get global.disable` confirmed `[tool.rumdl]` discovery.
- Official sources:
  [rumdl repository and CLI overview](https://github.com/rvben/rumdl),
  [configuration discovery](https://github.com/rvben/rumdl/blob/main/docs/configuration/index.md),
  [MD051 rule](https://rumdl.dev/md051/),
  [GFM comparison](https://github.com/rvben/rumdl/blob/main/docs/markdownlint-comparison.md).

**Disposition:** adopt as the leading candidate for local Markdown/link checks;
keep formatter use separate. Pin the tested version and select a narrow rule set
 during integration.
