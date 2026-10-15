# 27. Use prototyping within Investigations

Date: 2026-10-15

## Status

Accepted

## Context

Investigation and Prototype both answer bounded questions. Their useful
difference is the method: feasibility may require exploratory implementation
rather than reading documentation or comparing candidates. Separate Work kinds
made that methodological distinction another contract and reading route.

## Decision

Use prototyping as a method within Investigation, retiring Prototype as a
separate Work kind. An Investigation can compare candidates or answer a
feasibility question through exploratory implementation. Its contract states
implementation limits and required observable evidence. Retain observed results,
including unsuccessful attempts, separately from assumptions.

Keeping Prototype as a kind makes exploratory implementation explicit, but
limits and method can be stated in the Investigation contract. Evaluation
continues to own empirical evidence under a declared protocol as decided by
[WDR 16](0016-use-evaluations-for-empirical-evidence.md); its role is unchanged.

## Consequences

One Investigation route covers recommendations and feasibility findings. A
successful prototype does not establish production readiness; production
adoption requires a separate reviewed contract addressing missing production and
integration requirements.
[Work definition](../work-definition.md#investigations) and the
[glossary](../ubiquitous-language.md) own the current meanings. The
[guidance Work](../feat/work-contract-migration/guidance/README.md) carries the
change; historical Prototype references retain their original meaning.
