# Acceptance test lifecycle

Review test ownership when completing a Work so temporary adoption evidence
does not become unnecessary permanent regression coverage.

## Acceptance criteria

- Establish a completion checkpoint in `doc/workflow.md` that reviews added
  tests before removing the Work's documentation.
- Put test ownership guidance in `doc/engineering.md`: remove temporary probes
  that only verify upstream behavior; retain tests for our integration,
  contracts, and concrete compatibility regressions. Review purpose rather than
  deleting every test involving a dependency.
- Preserve removed probes and their results in the delivery PR and Git history.
  A removed probe remains adoption evidence, not continuing regression coverage.
- Coordinate with
  [Acceptance traceability](../docs-checks/acceptance-traceability/README.md) so
  intentional removal of a verified temporary probe does not falsely mark its AC
  incomplete. Changed acceptance requirements still need fresh evidence.
- Demonstrate the rule on the rumdl adoption tests: identify which belong to
  our integration and which only probe the upstream tool, then review any
  removals and rerun retained relevant tests.
- Promote the lasting rules to their owners, mark this Work `DONE` in its
  parent, and remove this directory in the delivery PR.
