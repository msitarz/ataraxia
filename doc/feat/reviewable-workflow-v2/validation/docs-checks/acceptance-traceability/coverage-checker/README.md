# Coverage checker

Implement a small checker for coverage declarations on active Work contracts.
Use [acceptance tracing](../../../../../../acceptance-tracing.md); do not
redefine marker or TODO/DONE syntax.

## Acceptance

- Check that markers on active contracts refer to existing ACs and that each
  `DONE` AC has linked test coverage or an explicit non-test verification method
  stated beside it. Missing coverage remains `TODO`.
- Report declared coverage only. The checker does not run tests or query CI;
  CI gates test results, and review assesses whether tests or other methods
  establish the intended behavior.
- For a temporary probe removed while its AC remains active, follow
  [test ownership](../../../../../../test-ownership.md) and put the one-time
  method and delivery PR link beside that criterion.
- When a delivery PR removes a Work directory, compare the deleted contract
  with tests and other verification methods in that PR. Keep markers and
  docstrings on retained tests as durable behavior records; treat markers for
  removed contracts as historical, with Git history mapping their path and ID
  to the original AC.
