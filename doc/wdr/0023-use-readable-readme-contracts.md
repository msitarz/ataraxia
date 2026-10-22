# 23. Use readable README contracts

Date: 2026-10-15

## Status

Accepted

Amends
[1. Use Work directories as delivery contracts](0001-use-work-directories-as-delivery-contracts.md)
for contract structure and the single README owner. Directory identity and
co-located acceptance remain in force.

Amended by
[31. Define outcome contracts and size for understanding](0031-define-outcome-contracts-and-size-for-understanding.md).

## Context

The maintainer found Work contracts hard to read. Requirements were spread
across introductory prose, acceptance criteria, validation plans, and repeated
guidance. Rewriting validated-core and sandbox discovery around a common
outline made purpose, mechanisms, and individual outcomes easier to find.

## Decision

Use the [Work contract template](../work-contract-template.md) as the authoring
owner, with one `README.md` contract per Work. Each criterion defines one
coherent observable outcome; together the criteria fulfill purpose and goals.
Keep only relevant optional sections. Linked findings, protocols, and results
support the contract rather than define separate specification/design contracts.
[Work definition](../work-definition.md) retains context and specialized Work
requirements, linking general repair and lifecycle rules to their owners.

A free-form contract offers flexibility but makes readers reconstruct the
structure. Separate specification/design files distribute the contract without
a demonstrated need. The single template gives predictable navigation while
allowing detail to scale to the Work.

## Consequences

Authors have one place for structure and outcome prompts; reviewers can scan
individual outcomes without rebuilding the contract from guidance. Long
contracts still need scope review rather than more headings. Existing contracts
and tooling are migrated under the
[migration Work](https://github.com/msitarz/ataraxia/blob/a2125a2de7c4d9514d57069845e3b679d6974385/doc/feat/work-contract-migration/README.md);
this decision alone does not establish that migration is complete.
