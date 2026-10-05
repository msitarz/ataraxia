# Test ownership

Read this file when completing a Work or reviewing tests for cleanup, including
documentation tool probes.

Review the purpose of tests added during a Work. Remove temporary adoption
probes that only verify upstream behavior. Retain tests for our integration,
contracts, and concrete compatibility regressions, including tests that
exercise a dependency through our own boundary.

Before removing an upstream-adoption probe, preserve its one-time method and
observed results in the existing execution records or relevant report/artifact.
Identify any affected active criterion. Explain the removal rationale in the
cleanup commit message. Git retains the probe's code; its historical execution
evidence does not establish ongoing regression coverage or passing checks on
later revisions. Follow [acceptance tracing](acceptance-tracing.md) for
criterion status and completion evidence.
