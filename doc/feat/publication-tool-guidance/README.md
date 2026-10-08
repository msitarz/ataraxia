# Publication and tool discovery

Clarify two agent handoff boundaries: mechanical PR publication and when to
consult Make's target index. Preserve independent review, maintainer authority,
and the Make interface.

## Delivery map

- **TODO** [Publisher delegation](publisher/README.md): bound the mechanical
  publication role, its handoff, refusal points, and report.
- **TODO** [Make target discovery](tool-discovery/README.md): clarify when
  contributors consult `make help` and which owner maintains that route.

Merge this plan before either guidance leaf. The publisher leaf owns
`doc/pull-requests.md` and its concise orchestrator route; the tool-discovery
leaf owns the `AGENTS.md` route and its `CONTRIBUTING.md` owner. Keep the two
changes separate and preserve existing review and CI gates.

## Acceptance

- **AC-1 TODO** Given both guidance contracts, their responsibilities and
  boundaries preserve independent artifact review, publication authority,
  discoverable Make commands, and the existing delivery gates.

  Validation: manually review both child scopes and owners against PR,
  orchestrator, Make, contributor, and workflow-record guidance.
