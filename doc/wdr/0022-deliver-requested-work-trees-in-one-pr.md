# 22. Deliver requested Work trees in one PR

Date: 2026-10-12

## Status

Accepted

Amends
[12. Orchestrate Work trees by responsibility](0012-orchestrate-work-trees-by-responsibility.md)
for execution and integration, and
[21. Publish after local Work acceptance](0021-publish-after-local-work-acceptance.md)
for the requested-tree publication boundary. Amended by
[28. Retain Work contracts until authorized closure](0028-retain-work-contracts-until-authorized-closure.md).
Independent review, role-policy ownership, observed acceptance, final-head full
CI and maintainer control remain in force.

## Context

The
[approved requested-tree contract](https://github.com/msitarz/ataraxia/blob/fafd6330f8364fc78052761d7f82ac3674e8f0c0/doc/feat/work-tree-delivery/README.md)
extends existing responsibility boundaries to bounded local leaf reviews and one
final delivery. Separate child PRs require intermediate publication and merge
coordination even when local acceptance can support dependent work. Publishing
only at the requested Work boundary keeps that coordination local; it requires
explicit integration review and preserved contract history. No speed or cost
benefit is established by this choice.

## Decision

The maintainer's requested Work owns publication. Direct leaves run sequentially
with the same executor/session in one accumulating isolated tree; child parents
use separate isolated trees and assigned base refs. Independent ready subtrees
may run in parallel with shared edits coordinated serially. Complete leaf
reviews remain bounded, while parent review assesses interfaces and composition.

Preserve each leaf's reviewed verification/cleanup pair. A child parent retains
its verified contract until its immediate parent reviews integration, then that
parent records child cleanup and its map update. Integrate these commits as
linear history and complete the requested Work's own reviewed pair. Publish one
final PR for that requested Work; a requested leaf keeps its usual PR flow.
Corrections and CI-specific acceptance retain WDR21's gates. New splits and
needed maintainer decisions pause the entire requested tree safely.

Current execution and integration rules belong in
[orchestrator guidance](../orchestrator.md), local history and evidence in
[acceptance tracing](../acceptance-tracing.md), planning in
[Work workflow](../workflow.md), and publication in
[pull-request guidance](../pull-requests.md).

## Consequences

Local acceptance can unblock dependencies without child publication or a
`master` merge. Parent owners carry integration and shared-edit coordination;
retained contracts and ordered pairs preserve inspectable acceptance. A larger
final parent diff requires composition review while its leaves retain bounded
reviews. Explicit CI-dependent criteria may require maintainer steering before
cleanup. Existing operational roles and tools remain unchanged.
