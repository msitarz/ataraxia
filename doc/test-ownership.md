# Test ownership

Read this file when completing a Work or reviewing tests for cleanup, including
documentation tool probes.

Review the purpose of tests added during a Work. Remove temporary adoption
probes that only verify upstream behavior. Retain tests for our integration,
contracts, and concrete compatibility regressions, including tests that
exercise a dependency through our own boundary.

Record removed probes, their one-time verification method and result, and the
removal rationale in the delivery PR. When removal affects an active acceptance
criterion, identify that criterion in the PR evidence. Keep the planned
`Verification:` clause in the Work contract unchanged when recording the
result. The PR record is the evidence for the removed probe; see the
[acceptance evidence rules](acceptance-tracing.md#planned-verification-and-evidence).
A removed probe is adoption evidence, not continuing regression coverage; its
code and result remain available in Git history and the PR.
