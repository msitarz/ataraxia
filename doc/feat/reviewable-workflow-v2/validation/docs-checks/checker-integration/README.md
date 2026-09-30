# Checker integration

Adopt rumdl for Markdown formatting and offline checks. Agents use supported
targets rather than writing ad hoc formatting or link-checking scripts.

Pin rumdl 0.2.78 in the development toolchain. Configuration in `pyproject.toml`
owns rule selection, with MD051 and MD057 enabled, and prose reflow enabled at
80 columns. Keep code blocks and long URLs exempt from wrapping. Use one policy
for local commands and CI.

## Acceptance scenarios

IDs are scoped to this README. Implement the CLI scenarios with plain pytest
and temporary Markdown fixtures; invoke rumdl rather than reimplementing its
parser or link resolver.

- **AC-1 — Prepared offline tools:** After `make setup`, formatting and checks
  run with network access disabled and without synchronizing dependencies.
  Missing tooling fails visibly instead of installing or silently skipping it.
- **AC-2 — Command discovery:** `make help` lists check-only `make doc-check`
  and modifying `make doc-format`, with accurate side-effect descriptions.
- **AC-3 — Formatting:** A fixture with long prose, irregular table spacing,
  and missing heading/list spacing is formatted by `make doc-format`. Prose
  follows the configured width; content and link destinations are preserved.
  A second run leaves the file byte-for-byte unchanged.
- **AC-4 — Protected content:** Formatting preserves Mermaid and other fenced
  code bodies, inline code, and YAML frontmatter values. Frontmatter acceptance
  does not claim schema validation.
- **AC-5 — Check-only behavior:** `make doc-check` succeeds for compliant input
  and fails for formatting violations without modifying files. Formatting that
  input makes the formatting checks pass.
- **AC-6 — Local navigation:** Existing relative files, directories, same-file
  headings, cross-file headings, and duplicate-heading `-1` anchors pass.
  Missing files and missing heading fragments fail with file/rule diagnostics.
- **AC-7 — Literal examples and external links:** Apparent broken links inside
  inline code and fenced examples do not fail link checks. External URLs are
  not fetched; local checks remain functional offline.
- **AC-8 — Selection:** No arguments check or format all repository Markdown,
  excluding environments, caches, and generated artifacts. `ARGS` accepts file
  or directory paths; formatting changes only selected files. Link validation
  still checks the full document graph so inbound links broken by a selected
  heading rename or deletion fail.
- **AC-9 — CI parity:** Local verification and CI invoke the same check-only
  target and configuration. A broken local link or formatting violation fails
  the documentation gate; CI never rewrites files.
- **AC-10 — Agent guidance:** Permanent routing and documentation ownership
  guidance direct agents to these targets for Markdown formatting and link
  checks. Agents write content and repair reported targets; no custom scripts
  duplicate tool-provided formatting or link resolution.

## Delivery boundaries

Keep the initial repository formatting baseline in a separate reviewable change
from tool/configuration integration. Complete this Work once that baseline and
the common gate pass. Add repository-specific semantic rules, such as recursive
README contracts and path identity, in later small Works when needed. Do not
adopt other Markdown or prose engines in this Work.
