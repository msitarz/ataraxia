# Repository Guidelines

Do not read root repository README.md. It is for humans only.

## Roles

The primary agent in the maintainer’s conversation is the orchestrator,
regardless of its model. Model selection does not assign a role: a Luna primary
agent must orchestrate and delegate just as a Sol primary agent does. A request
to implement, fix, clean up, publish, or define work does not itself assign the
executor, cleaner, publisher, or definer role. Only an explicit role assignment
by the maintainer or a parent agent changes your role. Orchestrators must
delegate those activities and follow `doc/orchestrator.md`. Every delegated
handoff must explicitly assign the subagent’s role.

## Task routing

Use this table to find the guidance that applies to the task. Read the glossary
entries relevant to the task; read it in full when defining shared terms or
recovering context that requires them. For a Work, follow the route below and
its relevant README and linked contracts.

| Task | Read or run |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| Any repository change | [Repair and scope rules](doc/change-rules.md#fix-the-underlying-problem) |
| Acting as orchestrator for changes | [Orchestrator handoffs](doc/orchestrator.md) |
| Acting as definer for a Work contract | [Definer guidance](doc/definer.md) |
| Acting as executor for changes | [Executor guidance](doc/executor.md) |
| Code or tests | [Engineering judgment in review](doc/engineering-review.md), [Engineering conventions](doc/engineering.md), [architecture](doc/architecture.md) for current contracts, and relevant [ADRs](doc/adr/) |
| Writing, changing, or reviewing tests | [Testing](doc/testing.md), then the relevant test-type guidance |
| Test cleanup | [Test ownership](doc/test-ownership.md), including documentation tool probes |
| Documentation | [Documentation ownership](doc/README.md); use `make doc-check` and `make doc-format` for Markdown formatting and local links |
| Empirical evaluation | [Empirical evaluations](doc/evaluation.md) and the specific Work README and protocol |
| Defining or reviewing a Work contract | [Work contract template](doc/work-contract-template.md), [Work definition](doc/work-definition.md), and the relevant Work README |
| Work | [Work workflow](doc/workflow.md) and the relevant Work README |
| Post-merge branch cleanup | [Branch cleanup](doc/branch-cleanup.md) after the maintainer confirms a Work PR merged |
| Work acceptance and delivery evidence | [Work acceptance](doc/acceptance-tracing.md) |
| Architectural boundary or decision | [Architecture](doc/architecture.md), relevant [ADRs](doc/adr/), and [ADR workflow](doc/adr-workflow.md) |
| Consequential delivery-workflow decision | [WDR workflow](doc/wdr-workflow.md) and relevant [WDRs](doc/wdr/) |
| Running project tools | [Make targets and discovery](CONTRIBUTING.md#make-targets) |
| Setup, branches, or commits | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Publishing or describing pull requests | [Pull requests](doc/pull-requests.md) |
| Choosing checks or reporting evidence | [Check and evidence policy](doc/validation.md) |
| CI jobs | [CI workflow](.github/workflows/ci.yml) |
