# Work structure and review

Use the same directory and review pattern recursively for a legacy feat slice,
a larger Work, or a small delivery increment. Nest when it reduces the context
needed for a decision; aim for shallow trees and strongly discourage more than
five levels. Directory nesting does not choose a Git base.

The parent README maps its immediate children with one list item per Work:

```markdown
- **TODO** [Child](child/README.md)
- **DONE** Child — delivered outcome
- **ABORT** Child — reason for stopping
```

`TODO` points to an existing directory. A Work's delivery change replaces its
parent's `TODO` item with `DONE` and removes the child's directory in the same
PR. If a Work is abandoned, replace it with `ABORT`, give a reason, and remove
the directory. Terminal items need no child link. The parent README is the
local status map while that parent exists; PRs hold review discussion and Git
holds the removed contracts and exact changes. Promote lasting behavior and
decisions to their owning code, tests, documentation, or ADRs before removing a
finished parent, including a top-level feat. No permanent root status index is
required.

## Works

- **TODO** [Local contracts](local-contracts/README.md)
- **TODO** [PR review and merge gates](pr-gates/README.md)
- **TODO** [Experiments and rewrites](experiments-and-rewrites/README.md)
