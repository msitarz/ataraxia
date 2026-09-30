# Mado

**Pros:** Rust Markdown linter; supports CommonMark and GFM, and implements many
markdownlint rules. The upstream README documents a GitHub Action and CI.

**Cons:** The documented CLI is `mado check`; no format/fix command is
documented. No local file or heading-anchor link-check rule is listed (MD051 is
absent from the
[supported-rule table](https://github.com/akiomik/mado/blob/main/README.md#supported-rules)).
It is a standalone binary, not a Python package supplied through this
repository’s pinned `uv` toolchain, so adoption needs a separate install and
version-pinning step. Front matter is not documented as a special construct.

**Evidence:**
[Upstream README](https://github.com/akiomik/mado/blob/main/README.md) documents
`mado check .`, CommonMark/GFM support, and releases/Actions. Runtime was not
tested; Mado is not installed. Capability conclusions come from the documented
interface and rule list. Check mode is read-only by interface, so it should
preserve Mermaid fences and front matter, but behavior on this repository’s
files remains unverified. **Decision: defer** because it does not meet the
local-link validation need.
