# Decision record format

Read when writing or reviewing an Architecture Decision Record (ADR) or
Workflow Decision Record (WDR). The ADR and WDR workflows own eligibility,
reading routes, and their separate indexes; this file owns their shared record
format and lifecycle.

## One decision per record

Each record captures one decision that can be accepted, rejected, or replaced
independently. Keep supporting mechanics and consequences of one decision
together.

## Record format

Use the next unused number in the collection and the filename
`NNNN-kebab-case-title.md`. Start the file with `# N. Title`, `Date:
YYYY-MM-DD`, then these sections:

```markdown
## Status

Accepted

## Context

...

## Decision

...

## Consequences

...
```

Every ADR or WDR in a ready PR carries `Accepted` as its intended merged state,
including records delivered by an Investigation. The maintainer accepts the
decision through merge; ready status alone does not establish maintainer
approval, acceptance, or completed implementation. Use `Proposed` only during
unpublished drafting. Follow
[PR publication rules](pull-requests.md#descriptions) for readiness; draft PRs
are not published.

Keep records concise. Put meaningful alternatives, tradeoffs, links to current
guidance, and the relevant PR or Work in the appropriate section. Use relative
Markdown links.

## Amendments and supersession

Preserve accepted records. Change an accepted decision with a new record that
links back to it. For a partial change, use `Amends [N. Title](NNNN-title.md)`
under Status and explain what remains in force. On acceptance, add reciprocal
`Amended by [M. Title](MMMM-title.md)` to the earlier record. For replacement,
use `Supersedes` in the new record and `Superseded by` in the earlier record.
Keep records in their respective collections. Ship the matching index entry and
any reciprocal amendment or supersession metadata in the same adoption PR, so
the intended merged state is consistent without a follow-up.
