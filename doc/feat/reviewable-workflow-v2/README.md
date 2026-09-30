# Reviewable workflow v2

Build a delivery workflow around small PRs that the maintainer can inspect in
about five minutes, discuss, and steer. Each work unit has a directory and a
short `README.md`. Its PR carries review evidence and discussion; Git records
the exact changes. Larger units group smaller ones without maintaining a fixed
step list or journal.

## Work units

- **DONE** Guidance and routing — moved rules to their owners, routed agents by
  task, and retired the superseded workflow.
- **TODO** [Review units](review-units/README.md): define local contracts,
  branches, PRs, approval, and trunk integration.
- **TODO** [Validation](validation/README.md): use focused draft checks and
  evaluate mechanical documentation checks.
- **TODO** [Live trial](live-trial/README.md): use this workflow during its own
  delivery, then apply it to a familiar feature.

These entries map known work, not a required execution order. New child units
can be added as discoveries warrant. The parent list shows each child's status
on the checked-out branch; use `master` for integrated status. Merge this map to
`master` before starting unit PRs that edit it.
No active repository guidance changes in this first artifact.
