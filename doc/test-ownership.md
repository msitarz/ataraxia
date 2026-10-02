# Test ownership

Read this file when completing a Work or reviewing tests for cleanup, including
documentation tool probes.

Review the purpose of tests added during a Work. Remove temporary adoption
probes that only verify upstream behavior. Retain tests for our integration,
contracts, and concrete compatibility regressions, including tests that
exercise a dependency through our own boundary.

Record removed upstream-adoption probes, their one-time method and result, and
the removal rationale in the delivery PR; identify any affected active
criterion. Their code and result remain in Git and the PR, but are not ongoing
regression coverage. See [acceptance tracing](acceptance-tracing.md) for
criterion status and completion evidence.
