# Workspace preparation

Measure and document a minimal Make-owned preparation path for docs-only agent
workspaces, or demonstrate evidence-based reuse of an existing prepared
environment and caches. Do not permit unchecked sharing of mutable virtual
environments.

Keep locked dependency synchronization, clear missing or stale environment
failures, hooks and packaging for their actual consumers, offline verification
promises, and the full audit intact. The trial-preparation map tracks the
existing CI-preparation outcome; [Make](../../../../../../Makefile) owns its
recipes. Declare the dependency and order for overlapping Make edits:
deliver CI preparation first or explicitly coordinate changes. Do not create a
second CI optimizer. Measure cold and warm preparation where meaningful; do
not promise unmeasured gains.

## Acceptance

- **AC-1 TODO** The docs-only agent path is minimal and Make-owned, or reuse is
  backed by evidence and does not share an unchecked mutable environment.
  Verification: inspect the declared Make path and exercise it in a
  docs-only workspace or inspect comparable reuse evidence.
- **AC-2 TODO** Locked dependencies, stale/missing failures, consumer-required
  hooks and packaging, offline guarantees, and the full audit remain intact.
  Verification: review affected Make behavior and report focused setup or
  verification evidence for each affected boundary.
- **AC-3 TODO** Overlap with CI preparation has an explicit delivery order or
  coordination and does not duplicate its optimization. Any claimed gain has
  cold/warm evidence where meaningful.
  Verification: inspect the child
  dependency/order and compare reported measurements with the declared basis.
