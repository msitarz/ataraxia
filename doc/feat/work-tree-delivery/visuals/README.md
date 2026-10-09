# Describe meaningful changes visually in Work contracts

After the first three leaves, own this guidance at
[Work workflow](../../../workflow.md), linking authoritative
[acceptance tracing](../../../acceptance-tracing.md) rather than introducing
another acceptance procedure. Require proportionate visuals for meaningful
architecture, package/module relationships, interactions or lifecycle changes.
Verify the current state before describing it; show proposed additions, changes
and removals against that verified before state. Include compact affected public
API descriptions for functions, classes and data structures, with useful
signatures and behavior when they help review. Distinguish proposed behavior
from verified existing behavior.

Choose appropriate GitHub-supported Mermaid types for the subject, including
sequence, class or state diagrams when suitable rather than requiring only
flowcharts. Tiny edits may use clear prose. Put shared context in the parent
overview and affected detail in the local leaf, with links instead of duplicate
diagrams. Visuals support the owned contract and acceptance evidence; they do
not establish acceptance or override criteria.

Add a small set of examples covering relationships, interactions/lifecycle,
public API changes and a prose-only tiny edit. Include a render check
appropriate to GitHub's supported syntax alongside content review of
before/after accuracy. Keep the complete guidance/example change within about
five-minute review; no tooling, mandatory template or unrelated retrospective
Work edits.

- **AC-1 TODO** Given a meaningful structural, interaction, lifecycle or public
  API change, reviewed Work guidance yields accurate proportionate before/after
  descriptions with suitable visuals and compact API detail; tiny changes and
  parent/leaf placement remain clear without duplicated context or weakened
  acceptance ownership.

  Validation: manually review the examples and render their Mermaid using a
  GitHub-compatible renderer; trace verified current/proposed states, changed
  APIs and parent/leaf links, then run doc/ac checks.
