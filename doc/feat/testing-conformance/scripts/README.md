# Script testing boundaries

Preserve registry, acceptance-tooling, and commit-hook contracts while applying
[testing guidance](../../../testing.md) at the smallest observable boundary.

The next planning delivery defines bounded leaves for registry CLI relocation,
registry record contracts, registry payload contracts, acceptance command
construction, acceptance declarations, and commit-message boundaries.
Subprocess cases belong in integration; pure selectors remain units. Use
complete independent manifests, precise failures, unchanged-output assertions,
real source fixtures, explicit process environments, isolated Git configuration,
and timeout-owning helpers. Preserve actual hook and prek integration coverage.

Keep shared registry arrangements owned by the script suite with narrow Make
reuse. Sequence changes to those arrangements and acceptance helpers with their
Make consumers; retain Work markers when tests move.
