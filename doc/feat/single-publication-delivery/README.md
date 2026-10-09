# Review both delivery commits before publication

Adopt the maintainer-selected sequence: focused local validation and independent
orchestrator review, separate verification and cleanup commits, review both,
then one publication and full CI on the final reviewed head before merge.
Retain role boundaries, five-minute scope, correction tracking and maintainer
merge authority. Session authorization does not complete lasting guidance.

- **TODO** [Delivery policy adoption](policy/README.md): reconcile acceptance,
  publication and CI owners, affected active validation wording, and WDR 21.

This plan changes no guidance or criterion status. Coordinate shared Compute
parent edits with its active deliveries and preserve independently delivered
statuses. Split the adoption before expansion if the complete supporting diff
exceeds five-minute review.

- **AC-1 DONE** Given adopted guidance and affected contracts, ordinary delivery
  can publish its independently reviewed two-commit sequence once, preserving
  verified acceptance and final-head CI/maintainer gates without treating
  pending CI or unsupported criteria as complete.

  Validation: manually review the child owners, active-contract reconciliation
  and WDR against ordinary delivery, explicit CI-dependent acceptance and later
  correction examples.
