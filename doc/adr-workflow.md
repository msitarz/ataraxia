# Architecture decision workflow

Read this file when considering, recording, or reviewing an architectural
decision.

- Check current code and relevant ADRs before treating a proposed direction as
  implemented behavior.
- For product architecture, use [product architecture](architecture.md).
- For repository workflow or tooling, use its owning guidance and source.

The [WDR workflow](wdr-workflow.md) owns consequential delivery-workflow
decisions.

## What warrants an ADR

- Create an ADR only for a consequential architectural choice whose rationale
  future work needs to preserve.
- Explain its architectural impact, meaningful alternatives, and the finding or
  constraint that motivates it.

Execution models, module boundaries, resource ownership, and durable storage or
external contracts can qualify; their importance must be explained, not inferred
from the category.

- Return types, helper classes, signatures, and internal representations
  ordinarily belong in code, tests, or the relevant Work contract.
- Mention code when it explains a qualifying decision, not to turn every
  implementation choice into an ADR.

[ADR 16](adr/0016-source-manages-its-own-provider-lifecycle.md)
qualifies because it changes resource ownership and cleanup guarantees after a
lifecycle finding, not merely because it moves a context manager.

- Corrections that conform to an established contract need no new ADR.
- Do not turn recovery from an implementation mistake into an architectural
  decision.
- Preserve older accepted records even when today's eligibility guidance would
  differ.

## ADRs per delivery

Apply the shared
[one decision per record](decision-records.md#one-decision-per-record) rule to
qualifying architectural choices. A Work may create zero, one, or several
ADRs; the number of implementation choices does not determine it.

## Record and change decisions

1. Search `doc/adr/` for the problem and related decisions.
   - Read covering records and follow amendment/supersession links.
   - Reuse them instead of duplicating decisions.
   - For product architecture, read [product architecture](architecture.md)
     before changing boundaries.
   - For workflow or tooling, consult the respective owner and source.
2. Follow the applicable delivery workflow for tracking and approval.
   - For a Work, use its local contract and the [Work workflow](workflow.md).
   - Record uncovered decisions before implementing the affected design.
   - Reassess when implementation reveals new choices.
3. Use the shared [decision record format and lifecycle](decision-records.md)
   for numbering, [ready-PR status](decision-records.md#record-format), and
   amendment or supersession links.
4. Update affected Work links and architecture's status references.
   - Link to the decision.
   - Do not copy its rationale or local specification into them.

## Writing

Follow the shared [writing standard](README.md#writing) and the shared
[decision record format](decision-records.md#record-format).

- Match the maintainer's direct, practical voice.
- Use short sentence-case titles that name the choice.
- Use plain, concrete language and correct grammar.
- Contractions and blunt sentences are natural.
- Reread the closest ADR before drafting:
  [0014](adr/0014-sink-module-file-special-attribute.md) for concise style,
  [0012](adr/0012-source-node-computable-instance.md) for a tradeoff, or
  [0016](adr/0016-source-manages-its-own-provider-lifecycle.md) for lifecycle
  changes.
- Scale detail to the problem.
- In Context, explain current behavior and what breaks, becomes awkward, or
  creates work for the quant.
- In Context, include useful examples and links to prior decisions.
- In Decision, state the choice, why it is preferred, and meaningful
  alternatives and tradeoffs.
- In Consequences, state costs, capabilities, drawbacks, and deferred work
  without repeating the decision; one sentence can suffice.
- Use first person only for the maintainer's stated reasoning.
- Do not invent personal history or experiments.
- Compare the draft with the related ADR and remove padding, corporate language,
  inflated benefits, generic introductions, exhaustive templates, and
  manufactured quirks.
