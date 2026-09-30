# Markdown formatting baseline

Apply the adopted rumdl formatting policy to every tracked Markdown file in
the repository, establishing a clean baseline for future documentation checks.
Begin after the parent Work supplies the pinned tool, shared configuration,
and `make doc-format` target.

## Acceptance criteria

- Run `make doc-format` across repository Markdown, including root guidance,
  documentation, ADRs, and Markdown templates. Exclude generated artifacts,
  environments, and caches according to the owning tool configuration.
- Use the shared configuration without introducing local overrides or ad hoc
  formatting scripts. A second formatter run produces no changes.
- Preserve meaning, acceptance requirements, link destinations, inline code,
  fenced code and Mermaid bodies, and YAML frontmatter values. Historical
  documents receive formatting changes only.
- Keep the PR focused on the mechanical baseline and this Work's lifecycle
  updates. Report semantic or broken-link findings separately rather than
  quietly changing contracts or suppressing checks to make the baseline pass.
- Run `make doc-check`; formatting checks pass. Resolve any outstanding link
  findings through separately reviewed changes before declaring this Work done.
- Review the resulting diff for content preservation, mark the parent's entry
  `DONE`, and remove this directory in the delivery PR.
