# Documentation ownership

Read this file when creating, changing, or reviewing documentation. It owns
placement and maintenance rules; [AGENTS.md](../AGENTS.md) routes tasks to the
relevant guidance.

## Owners

| Information | Authoritative location |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Task startup and conditional reading routes | [AGENTS.md](../AGENTS.md) |
| Repair and scope rules for repository changes | [Change rules](change-rules.md) |
| Documentation placement, duplication, and shared terms | This file |
| Shared meanings and distinctions | [Ubiquitous language](ubiquitous-language.md) |
| General Work rules | [Work workflow](workflow.md) |
| Post-merge Work branch cleanup | [Branch cleanup](branch-cleanup.md) |
| A Work's local outcome and acceptance contract | The relevant Work README |
| Orchestration and delegated repository changes | [Orchestrator handoffs](orchestrator.md) |
| ADR eligibility and architectural decision process | [ADR workflow](adr-workflow.md) |
| Shared ADR/WDR record format and lifecycle | [Decision record format](decision-records.md) |
| Workflow decision eligibility, routing, and index | [WDR workflow](wdr-workflow.md) |
| Coding, typing, and testing conventions | [Engineering](engineering.md) |
| Test ownership and cleanup | [Test ownership](test-ownership.md) |
| Work acceptance IDs, coverage markers, and test lookup | [Acceptance tracing](acceptance-tracing.md) |
| Setup, toolchain, contribution, and commit rules | [CONTRIBUTING.md](../CONTRIBUTING.md) |
| PR publication, descriptions, review states, and merge authority | [Pull requests](pull-requests.md) |
| Choosing checks and reporting validation evidence | [Validation](validation.md) |
| Markdown formatting and local-link checks | [Make targets](../Makefile) and [rumdl configuration](../pyproject.toml) |
| Current system relationships, boundaries, and limitations | [Architecture](architecture.md) |
| Introduction, runnable example, and roadmap priorities | [README.md](../README.md) |
| One architectural choice and its rationale | The relevant [ADR](adr/) |
| One delivery-workflow choice and its rationale | The relevant [WDR](wdr/) |
| Issue body format | [Issue template](../.github/ISSUE_TEMPLATE/work-item.md) |
| Machine-enforced settings and executable checks | Their configuration and implementation, including [pyproject.toml](../pyproject.toml), [Makefile](../Makefile), and [tach.toml](../tach.toml) |

## Placement and maintenance

Find the owner before adding information. Give independently triggered guidance
a focused owner and clear reading trigger. Route directly to that owner, then
link from broader documents without repeating its rules. Navigation summaries
may name a capability and its status, but must not repeat defaults, schemas,
lifecycle rules, or
procedures. Examples may demonstrate a contract without becoming a second
definition. Derive deterministic information from executable configuration
where practical; documentation explains its use rather than maintaining another
settings inventory.

Keep `AGENTS.md` a short entry point. Add guidance to its existing owner. Create
a document only for a distinct responsibility with a clear reading trigger; add
a route only when existing routes cannot discover it. Do not split files just
to move their size elsewhere or create a chain of indexes agents must read for
every task.

When adding or changing a reading route, check whether its target contains
guidance unrelated to the triggering task. Extract independently triggered rules
into a focused owner before routing there. Follow linked guidance only when its
stated reading trigger applies; a link alone does not require reading the
target.

Separate current guidance, proposed behavior, accepted decisions, implemented
behavior, and evidence. Accepted ADRs and WDRs explain decisions, not
implementation status. Verify current behavior in code and tests. If behavior
conflicts with an approved contract, surface the mismatch rather than treating
implementation as the intended design. Resolve inconsistent copies at the owner
and remove or link the others; do not add an exception to reconcile them.

Keep accepted ADR and WDR history intact, using the [ADR
workflow](adr-workflow.md) or [WDR workflow](wdr-workflow.md) to change
decisions. A new change owns its own evidence. Issue and PR records link to
detailed scope and evidence rather than copying it.

## Vocabulary

Check the [glossary](ubiquitous-language.md) before introducing a term. Define
new shared terms there before using them in specifications or implementation:
state their meaning, responsibility, distinctions, relationships, and essential
units or lifecycle rules. Keep delivery workflow language separate from
computation and trading language. Works and trading Features have distinct
definitions; local Work rules belong in their own contracts, with glossary
entries linking rather than reproducing those rules.

Use the glossary term consistently for each shared concept; avoid synonyms that
suggest an undefined distinction.

Reuse abstractions when their meaning fits. Qualify terms at boundary mappings.
Resolve ambiguity from the request and repository; if interpretations still
imply materially different behavior, present concrete alternatives before
implementation. Do not invent domain rules. Consistent naming needs no
approval.

## Review

Check ownership and duplication when defining or reviewing a Work, and when
changing general guidance. Verify local links and anchors, distinguish
history from current instructions, and walk through affected reading routes.
Check that moved requirements remain discoverable and examples agree with their
owning contracts. Run `make doc-check` to check Markdown formatting and local
links; run `make doc-format` to apply the configured formatting. Check that
prose, headings, and examples use the same glossary terms. Follow
[repair and scope rules](change-rules.md#fix-the-underlying-problem) for
cohesive changes.

Background:
[Thoughtworks](https://www.thoughtworks.com/insights/blog/evolutionary-architecture/domain-driven-design-in-10-minutes-part-one),
[Fowler and Joshi](https://martinfowler.com/articles/convo-llm-abstractions.html),
[Schleicher](https://www.danielschleicher.com/software/engineering,/ai,/spec-driven/development/2026/01/04/removing-ambiguity-with-spec-driven-development.html).
