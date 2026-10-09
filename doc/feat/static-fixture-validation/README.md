# Validate static expectations only as needed

Reviewed repository-owned static expectations need complete comparison with
actual values, rather than a second schema/content validator by default. The
maintainer has adopted this rule for the current session; lasting guidance
remains undelivered until the child completes review and delivery.

- **TODO** [Guidance reconciliation](guidance/README.md): define the distinction
  at common testing/type owners and reconcile directly conflicting CLI
  contracts.

The motivating example is PR #244's `test/ataraxia/cli_result_inputs.py` loader
for `fixtures/cli/reporting_expected.json`. A schema-shaped loader can duplicate
the reviewed expected fixture's content when its consumer only needs whole-value
equality. This is context for the guidance choice, not authorization to change
that PR, its tests, or any production validation. Assess actual consumer need
before any later implementation change.

- **AC-1 TODO** Given adopted guidance, agents can distinguish opaque comparison
  values from meaningful structured contracts across product, Make and script
  tests without duplicate validation or weakened independent expectations.

  Validation: independently review the child guidance and directly affected
  reading routes against whole-value equality, structured access and genuine
  external/validation-boundary examples.
