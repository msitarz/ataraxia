# Reviewable workflow v2

Build a delivery workflow around small PRs that the maintainer can inspect in
about five minutes, discuss, and steer. Each work unit has a directory and a
short `README.md`. Its PR carries review evidence and discussion; Git records
the exact changes. Larger units group smaller ones without maintaining a fixed
step list or journal.

## Work units

- [Guidance and routing](guidance/README.md): move rules to their
  owners and make agent reading selective.
- [Review units](review-units/README.md): define local contracts,
  branches, PRs, approval, and parent checkpoints.
- [Validation](validation/README.md): use focused draft checks and
  evaluate mechanical documentation checks.
- [Live trial](live-trial/README.md): use this workflow during its own
  delivery, then apply it to a familiar feature.

These directories map known work, not a required execution order. New child
units can be added as discoveries warrant. A child's presence in this candidate
tree does not mean its delivery PR has merged; inspect Git merge history for
that fact. No active repository guidance changes in this first artifact.
