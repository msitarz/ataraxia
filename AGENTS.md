# Repository guidelines

## Start every task here

Read [doc/ubiquitous-language.md](doc/ubiquitous-language.md) in full before
substantive discussion, planning, review, or implementation. Apply its vocabulary;
reread after context loss or compaction and when definitions change. Every agent
must do this. When delegating, include this requirement and relevant vocabulary
and contract references.

Inspect task-relevant code, tests, and decisions. Distinguish current behavior
from intended changes and surface discrepancies. Follow every applicable route
below before starting that work; read the owning guidance in full unless a
specific section is named. Routes are cumulative, not alternatives.

## Task routes

| Task | Read |
| --- | --- |
| Create, change, or review documentation or shared terms | [Documentation ownership](doc/documentation.md) |
| Define, implement, or review a feat slice | [Feat workflow](doc/feat-workflow.md), the slice, and applicable ADRs |
| Consider or change architectural decisions or boundaries | [ADR workflow](doc/adr-workflow.md), [architecture](doc/architecture.md), and relevant ADRs with amendment/supersession links |
| Change or review code, tests, tooling, or configuration | [Engineering conventions](doc/engineering.md) and relevant [architecture](doc/architecture.md) sections |
| Set up development or run validation | [CONTRIBUTING.md](CONTRIBUTING.md#prerequisites) through its toolchain policy |
| Create branches, issues, commits, or PRs | [Contribution procedure](CONTRIBUTING.md#submitting-a-change) and [commit conventions](CONTRIBUTING.md#commits-and-pull-requests); use the feat workflow when applicable |
| Understand usage or roadmap priorities | [README.md](README.md) |

Keep this file an entry point. Place new guidance through
[documentation ownership](doc/documentation.md#placement-and-maintenance).
