# Repository Guidelines

## Task routing

Use this table to find the guidance that applies to the task. Read the glossary
entries relevant to the task; read it in full when defining shared terms or
recovering context that requires them. For a Work, follow the route below and
its relevant README and linked contracts.

| Task | Read or run |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| Any repository change | [Repair and scope rules](doc/change-rules.md#fix-the-underlying-problem) |
| Acting as orchestrator for changes | [Orchestrator handoffs](doc/orchestrator.md) |
| Code or tests | [Engineering conventions](doc/engineering.md), [architecture](doc/architecture.md) for current contracts, and relevant [ADRs](doc/adr/) |
| Test cleanup | [Test ownership](doc/test-ownership.md), including documentation tool probes |
| Documentation | [Documentation ownership](doc/README.md); use `make doc-check` and `make doc-format` for Markdown formatting and local links |
| Work | [Work workflow](doc/workflow.md) and the relevant Work README |
| Work acceptance coverage | [Acceptance tracing](doc/acceptance-tracing.md) |
| Architectural boundary or decision | [Architecture](doc/architecture.md), relevant [ADRs](doc/adr/), and [ADR workflow](doc/adr-workflow.md) |
| Consequential delivery-workflow decision | [WDR workflow](doc/wdr-workflow.md) and relevant [WDRs](doc/wdr/) |
| Running project tools | Run `make help` first; invoke project tools through Make targets. |
| Setup, branches, commits, or pull requests | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Choosing checks or reporting validation evidence | [Validation policy](doc/validation.md) |
| CI jobs | [CI workflow](.github/workflows/ci.yml) |
