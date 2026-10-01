# Architecture decision workflow

Read this file when considering, recording, or reviewing an architectural
decision. Check [architecture](architecture.md), current code, and relevant
ADRs before treating a proposed direction as implemented behavior.

## What warrants an ADR

Create an ADR only for a consequential architectural choice whose rationale
future work needs to preserve. Explain its architectural impact, meaningful
alternatives, and the finding or constraint that motivates it. Execution models,
module boundaries, resource ownership, and durable storage or external contracts
can qualify; their importance must be explained, not inferred from the category.

Return types, helper classes, signatures, and internal representations
ordinarily belong in code, tests, or the feat slice. Mention code when it
explains a qualifying decision, not to turn every implementation choice into an
ADR. [ADR 16](adr/0016-source-manages-its-own-provider-lifecycle.md) qualifies
because it changes resource ownership and cleanup guarantees after a lifecycle
finding, not merely because it moves a context manager.

Corrections that conform to an established contract need no new ADR. Do not turn
recovery from an implementation mistake into an architectural decision. Preserve
older accepted records even when today's eligibility guidance would differ.

## ADRs per delivery

Apply the shared
[one decision per record](decision-records.md#one-decision-per-record) rule to
qualifying architectural choices. A feat slice may create zero, one, or several
ADRs; the number of implementation choices does not determine it.

## Record and change decisions

1. Search `doc/adr/` for the problem and related decisions. Read covering
   records and follow amendment/supersession links; reuse them instead of
   duplicating decisions. Read [architecture](architecture.md) before changing
   boundaries.
2. Follow the applicable delivery workflow for tracking and approval. The
   [legacy feat workflow](feat-workflow.md) retains its issue gate; Works use
   branches and PRs without routine issues. Record uncovered
   decisions before implementing the affected design, and reassess when
   implementation reveals new choices.
3. Use the shared [decision record format and lifecycle](decision-records.md)
   for numbering, status, and amendment or supersession links.
4. Update affected slice links and architecture's status references. Link to
   the decision; do not copy its rationale or local specification into them.

## Writing

Match the maintainer's direct, practical voice. Reread the closest ADR before
drafting: [0014](adr/0014-sink-module-file-special-attribute.md) for concise
style, [0012](adr/0012-source-node-computable-instance.md) for a tradeoff, or
[0016](adr/0016-source-manages-its-own-provider-lifecycle.md) for lifecycle
changes. Use short sentence-case titles naming the choice and plain, concrete
prose. Contractions and blunt sentences are natural; keep grammar correct. Scale
detail to the problem and prefer paragraphs unless a list or code clarifies it.

Context explains current behavior and what breaks, becomes awkward, or creates
work for the quant. Use useful examples and links to prior decisions. Decision
states the choice, why, meaningful alternatives, and tradeoffs. Consequences
states costs, capabilities, drawbacks, and deferred work without repeating the
decision; one sentence can suffice.

Use first person only for the maintainer's stated reasoning; never invent
personal history or experiments. Compare the draft with the related ADR and
remove padding, corporate language, inflated benefits, generic introductions,
exhaustive templates, and manufactured quirks.
