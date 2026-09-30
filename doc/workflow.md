# Work contracts

Read this file when creating, changing, or reviewing a Work.

Each Work lives in a directory identified by its repository path. Its short
`README.md` states the intended outcome and observable acceptance criteria so
the reviewer can tell when it is complete. Add `spec.md` or `design.md` only
when useful, and link to it from the README.

Use standard relative Markdown links. Use Mermaid when a diagram helps explain
behavior, relationships, or design choices; small changes do not need one.

Do not require fixed headings, YAML frontmatter, a journal, or separate
human-facing and agent-facing versions of the same contract.

## Lifecycle

A parent README maps its immediate child Works. `TODO` links to an active
child's README, `DONE` names the delivered outcome, and `ABORT` records why the
Work stopped. The child does not duplicate its parent-owned status.
Status entries describe the checked-out branch; use `master` to determine
integrated status. Merge a parent map to `master` before starting child PRs that
edit it.

Delivery or abandonment updates the parent's entry and removes the finished
child directory in the same PR. Before removing a finished Work, promote
lasting contracts and decisions to their authoritative owners. PRs hold review
discussion; Git preserves removed contracts and exact changes.

Discovery may add children without maintaining a fixed execution list. Nest
when it reduces necessary context; strongly discourage more than five levels.
Directory ancestry does not select a Git base.
