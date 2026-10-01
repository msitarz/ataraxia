# Retire the feat-slice workflow

Replace the active legacy feat-slice delivery workflow with the Work workflow
wherever no active legacy delivery depends on it. The repository currently has
no legacy slice directories outside this reviewable-workflow Work tree; verify
that status and inspect all references before deciding what to remove, migrate,
or preserve. Complete
[Workflow Decision Records](../workflow-decision-records/README.md) first so
consequential workflow decisions and useful history are preserved before
legacy guidance is pruned. After that Work removes its own directory, replace
this dependency link with the resulting permanent WDR guidance route.

Completion means:

- An inventory identifies active routes, terminology, role references, and
  unfinished legacy slices, and resolves each slice explicitly before its
  workflow is retired.
- Useful current requirements have one authoritative owner. Promote lasting
  rules to the relevant current owner, remove duplicate legacy guidance, and
  update direct routes in `AGENTS.md`,
  `CONTRIBUTING.md`, `doc/README.md`, the glossary, and ADR guidance as needed.
- Preserve delivered specifications and meaningful history. Choose deletion,
  archival, or a short historical pointer based on whether each artifact still
  needs to be discoverable; do not rewrite frozen acceptance contracts or leave
  broken links.
- Remove the active legacy workflow and its session-role definitions only
  after confirming they have no active use. Keep legitimate historical
  references understandable.
- Route future contributors directly to current owners. On completion, update
  the parent README to `DONE` with the delivered outcome and remove this child
  directory in the same PR, following the Work lifecycle.

This Work changes repository guidance and historical documentation only; it
does not alter product code or implement a new delivery process.
