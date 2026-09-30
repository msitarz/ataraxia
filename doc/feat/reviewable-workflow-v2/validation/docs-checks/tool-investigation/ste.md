# stazelabs/ste

## Pros

- Go CLI for Markdown and text with sentence, passive-voice, and related prose
  rules. A built binary needs no Go runtime. MIT licensed.

## Cons

- Approved-word checking requires a user-supplied copyrighted ASD PDF and local
  index. Its default prose mode omits that check.
- Adds separate installation and version management. Some linguistic checks
  are heuristic; passing does not establish STE compliance.
- Does not replace Markdown formatting or link validation.

## Evidence and decision

Documentation review only; no binary was installed or tested. Upstream documents
`go install github.com/stazelabs/ste/cmd/ste@latest`; a future probe should pin
a revision instead.

Defer as an optional prose candidate until we decide which measurable prose
rules improve this repository's documents.

Source: [upstream README](https://github.com/stazelabs/ste).
