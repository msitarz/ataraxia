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
| Writing, changing, or reviewing tests | [Testing](doc/testing.md), then the relevant test-type guidance |
| Test cleanup | [Test ownership](doc/test-ownership.md), including documentation tool probes |
| Documentation | [Documentation ownership](doc/README.md); use `make doc-check` and `make doc-format` for Markdown formatting and local links |
| Empirical evaluation | [Empirical evaluations](doc/evaluation.md) and the specific Work README and protocol |
| Work | [Work workflow](doc/workflow.md) and the relevant Work README |
| Post-merge branch cleanup | [Branch cleanup](doc/branch-cleanup.md) after the maintainer confirms a Work PR merged |
| Work acceptance coverage | [Acceptance tracing](doc/acceptance-tracing.md) |
| Architectural boundary or decision | [Architecture](doc/architecture.md), relevant [ADRs](doc/adr/), and [ADR workflow](doc/adr-workflow.md) |
| Consequential delivery-workflow decision | [WDR workflow](doc/wdr-workflow.md) and relevant [WDRs](doc/wdr/) |
| Running project tools | Run `make help` first; invoke project tools through Make targets. |
| Setup, branches, or commits | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Publishing or describing pull requests | [Pull requests](doc/pull-requests.md) |
| Choosing checks or reporting evidence | [Check and evidence policy](doc/validation.md) |
| CI jobs | [CI workflow](.github/workflows/ci.yml) |
