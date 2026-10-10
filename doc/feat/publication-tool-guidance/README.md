# Publication and tool discovery

Clarify two agent handoff boundaries: mechanical PR publication and when to
consult Make's target index. Preserve independent review, maintainer authority,
and the Make interface.

## Delivery map

- **DONE** Publisher delegation: the mechanical publication role, handoff,
  refusal points, and report are defined in
  [publisher guidance](../../publisher.md) and WDR 19.
- **DONE** Make target discovery: help triggers, target reuse, and target-owned
  runtime environments are defined in
  [contributor guidance](../../../CONTRIBUTING.md#make-targets), with a concise
  AGENTS route.

Merge this plan before either guidance leaf. The publisher leaf owns
`doc/publisher.md`, its PR-owner links and concise orchestrator handoff; the
tool-discovery leaf owns the `AGENTS.md` route and its `CONTRIBUTING.md` owner.
Keep the two changes separate and preserve existing review and CI gates.

## Acceptance

- **AC-1 TODO** Given both guidance contracts, their responsibilities and
  boundaries preserve independent artifact review, publication authority,
  discoverable Make commands, and the existing delivery gates.

  Validation: manually review both child scopes and owners against PR,
  orchestrator, Make, contributor, and workflow-record guidance.
