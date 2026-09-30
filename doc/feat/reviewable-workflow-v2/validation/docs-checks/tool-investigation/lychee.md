# Lychee

## Pros

- Dedicated link checker for Markdown, with relative file links and optional
  heading-fragment checking. `--offline` blocks network requests.
- Supports prebuilt binaries, a GitHub Action, caching, and a separate online
  run for external links. Code-block links are opt-in.

## Cons

- Does not format Markdown or enforce document structure.
- Adds a separate binary and pin alongside the Python toolchain. Avoid adding
  it if rumdl's local checks already cover the repository's needs.
- Fragment checking needs explicit configuration and does not cover every
  target format or dynamically generated anchor.

## Evidence and decision

Documentation review only; no binary was installed or command tested. The
upstream interface supports `lychee --offline --include-fragments=anchor-only .`
for local checks. Probe a pinned release before adopting that invocation.

Keep as a fallback for local-link gaps, or a later scheduled external-link
check. Keep network checks out of the fast offline gate.

Sources:
[upstream documentation](https://github.com/lycheeverse/lychee#commandline-usage),
[command-line flags](https://lychee.cli.rs/guides/cli/).
