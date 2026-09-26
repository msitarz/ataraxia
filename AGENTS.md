# Repository Guidelines

## Start Every Task Here

Read [doc/ubiquitous-language.md](doc/ubiquitous-language.md) **in full at the start of every task**, before substantive discussion, planning, defining new terms, review, or implementation. Apply its vocabulary throughout. Reread after context loss or compaction and whenever definitions change. Every agent, including subagents, must do this; include the requirement and relevant vocabulary/contract references when delegating.

Then inspect task-relevant code, tests, and ADRs. Distinguish current behavior from intended changes and surface discrepancies affecting the task. Before changing architectural boundaries, read [doc/architecture.md](doc/architecture.md) and follow the [ADR workflow](#architecture-decision-records).

## Fix the Underlying Problem

Optimize for the user's complete outcome and ongoing maintenance cost. The smallest useful change may span code, tooling, tests, and documentation.

- Before adding instructions, exceptions, duplicated logic, or a workaround, trace why it is needed. Check whether the component responsible for the behavior can provide it directly. Existing behavior is evidence, not automatically the intended contract; resolve mismatches against the task and accepted decisions.
- Prefer one authoritative implementation or definition, with other paths calling, deriving from, or linking to it. Automate deterministic steps people would otherwise need to remember. For example, make `make ci` run all required checks; validate a shared invariant at its owning boundary; derive repeated configuration from its source.
- Make the smallest cohesive fix that removes the cause within the task's scope. Preserve intentional differences and compatibility requirements; avoid speculative abstractions and unrelated refactors. If a workaround is necessary, explain the constraint and remaining limitation.
- **Revert fundamentally wrong approaches before reimplementing.** When your change violates an established project contract or convention, revert the offending change and any compensating changes built on it. Preserve unrelated work. Reimplement the smallest correct solution from the restored baseline, following existing project conventions, then validate it. Do not retain unnecessary abstractions, checks, or documentation introduced to support the rejected approach. Use a targeted fix for an isolated defect in an otherwise sound design.
- Update affected callers, tests, and docs together. Verify the actual command, API, or user flow being recommended, including relevant failures. Do not weaken tests or redefine documented expectations merely to accommodate a defect. Before finishing, check whether the user still has to compensate manually for the problem.

## Repository Map

Ataraxia is a pre-alpha orchestrator for bar-by-bar trading backtests:

- `src/ataraxia/compute/`: computation graph and loop; sibling modules handle sources, providers, features, brokerage, backtesting, and CLI.
- `test/unit/`, `test/integration/`, `test/acceptance/`: tests by boundary.
- `example/`: crossover strategy and its tests; `sample/`: synthetic CSV data.
- [doc/feature/](doc/feature/): feature slices; [doc/adr/](doc/adr/): architectural decisions.

Execution is currently local, sequential, and single-source. Parallel execution, multi-source synchronization, and immutable artifact storage are planned; verify status in code before treating documents as implemented behavior.

## Commands and Validation

Use Python 3.14+, `uv`, and `make`. [Makefile](Makefile) defines executable checks; the [CI workflow](.github/workflows/ci.yml) invokes its shared targets. [CONTRIBUTING.md](CONTRIBUTING.md) covers contribution setup.

| Command | Purpose |
| --- | --- |
| `make setup` | Synchronize dependencies; install prek pre-commit and commit-message hooks |
| `uv sync --frozen --group dev` | Install locked dependencies without hooks, as CI does |
| `make lint` / `make format` | Ruff lint with automatic fixes / formatting |
| `make typecheck` | Strict Pyrefly checks on `src/` |
| `make test` | Pytest with branch coverage |
| `make ci` | Sync locked dependencies, audit packages, check lint/formatting/types, and run covered tests and examples |
| `uv run pytest example/` | Example tests, outside default discovery |
| `uv audit --frozen --preview-features audit` | Run the dependency audit alone |
| `uv build` | Build distributions with `uv_build` |

For code changes, run focused tests during development, then `make ci` for all CI checks. Report checks that could not run. Update and include `uv.lock` when dependencies change.

Run the sample strategy:

```sh
uv run ataraxia --sink example/crossover.py --shards-dir sample --output results.json
```

## Ubiquitous Language

The [glossary](doc/ubiquitous-language.md) is the single source of truth for shared terms. Use them consistently in discussion, specifications, identifiers, docstrings, tests, and examples; reuse existing abstractions when their meaning fits.

- Keep concepts distinct: a `Provider` supplies input, a `Source` exposes it to the graph, and a `Runner` executes a node. A runner is not an executor worker. Use "feature slice" for a delivery increment when "feature" could mean a composable calculation. Qualify terms and explain mappings at boundaries.
- Resolve ambiguity from the request and repository first. If plausible meanings still imply materially different behavior, present concrete interpretations to the user before implementing that behavior. Do not invent domain rules; routine naming consistent with established meanings needs no confirmation.
- Before introducing a concept, check for an existing term. Define any needed new term in the glossary **before using it in specifications or implementation**: meaning, responsibility, distinction from related terms, and relevant relationships, units, or lifecycle rules.
- Keep shared definitions in the glossary and feature-local rules in the slice. Refine definitions and affected code, tests, and docs together. Link to the glossary rather than duplicating it; use the ADR workflow for architectural choices and preserve historical records.
- Verify meaning through observable examples and tests, including relevant timing, units, state transitions, and failures. Check behavior and module boundaries, not just terminology.

Background: [Thoughtworks](https://www.thoughtworks.com/insights/blog/evolutionary-architecture/domain-driven-design-in-10-minutes-part-one), [Fowler and Joshi](https://martinfowler.com/articles/convo-llm-abstractions.html), [Schleicher](https://www.danielschleicher.com/software/engineering,/ai,/spec-driven/development/2026/01/04/removing-ambiguity-with-spec-driven-development.html).

## Writing Feature Slices

Write proportional specifications in `doc/feature/`, using short prose and examples; no user-story formula or Gherkin is required.

- Lead with the problem, code-verified current behavior, and observable user/library outcome. State status (`proposed`, `in progress`, or `validated`); link issues and applicable ADRs, including decisions discovered during implementation.
- Scope a small usable increment through the necessary components. Split larger work by scenario or capability. State non-goals, dependencies, correctness, failure handling, and tests; identify preparatory refactors and experiments separately.
- Give acceptance examples with preconditions, inputs, action, and expected outputs or side effects. Include main behavior, significant boundaries/failures, and behavior to preserve. Specify observable contracts so tests survive implementation changes.
- Separate required contracts from provisional design: interfaces, ordering, compatibility, and resource ownership where relevant. Sketch only enough design for feasibility and consequential tradeoffs; leave other internals open. During planning and implementation, ensure every relevant architectural decision is covered using the ADR workflow below.
- Name assumptions, risks, and open questions. For uncertainty that could invalidate the approach, propose a bounded experiment with an expected result and evidence that would challenge it. Record findings and revise the plan; an experiment is not a completed feature.
- Plan short steps with a working path and early feedback. Pair behavior changes with tests, preserve working behavior between steps, refine scenarios, and make scope/contract changes explicit.
- Separate validation plans from results. Identify focused, integration, or CLI checks at the appropriate boundary. Performance claims need a baseline, representative workload, measurement method, and success criterion. Mark validated only after acceptance criteria and required repository checks pass; record evidence and limitations.

Example: the same strategy and shards yield identical ordered results with one or two workers; a shard failure preserves an existing output file. These are acceptance contracts; executor classes and scheduling helpers belong in design notes.

Background: [Thoughtworks](https://www.thoughtworks.com/en-au/insights/e-books/modern-data-engineering-playbook/delivery-planning-principles), [Fowler](https://martinfowler.com/bliki/FeatureDevotion.html), [Beck](https://newsletter.kentbeck.com/p/canon-tdd), [Farley](https://www.davefarley.net/?page_id=50).

## Architecture Decision Records

Create an ADR only for a substantive architectural decision. Correcting types, tests, or implementation to conform to an established contract does not require a new ADR. Do not turn recovery from your own mistake into a new architectural decision.

1. Search `doc/adr/` for the problem and related decisions; read relevant records and follow amendment/supersession links. Reuse a covering ADR instead of duplicating it.
2. Record uncovered architectural decisions **before implementing the affected design**, including module boundaries, execution models, resource ownership, and persistent contracts. Recheck when implementation reveals new choices. Open an issue before non-trivial architectural work.
3. Use the next unused number and `NNNN-kebab-case-title.md`. Format: `# N. Title`, `Date: YYYY-MM-DD`, then `Status`, `Context`, `Decision`, and `Consequences`. Explain the problem, relevant alternatives/tradeoffs, choice, and consequences. Use `Proposed` while unsettled and `Accepted` once decided.
4. Change accepted decisions through new records; preserve earlier context, decision, and consequences. Use relative Markdown links:
   - Partial change: new Status says `Amends [N. Title](NNNN-title.md)`; on acceptance, add reciprocal `Amended by [M. Title](MMMM-title.md)` to the earlier record. Follow ADRs 0010/0011 and state what still applies.
   - Replacement: new Status says `Supersedes [N. Title](NNNN-title.md)`; on acceptance, set earlier status to `Superseded by [M. Title](MMMM-title.md)`, following [adr-tools](https://github.com/npryce/adr-tools).
5. Update slice links and `doc/architecture.md` to reflect the decision and implementation status.

### ADR Writing Style

Match the maintainer's direct, practical voice. Reread the closest related ADR before drafting; use 0014 for a small convention, 0012 for a tradeoff, and 0016 for a lifecycle change.

- Use short sentence-case titles naming the choice and plain, conversational English with concrete code/domain terms. Contractions and occasional blunt sentences are natural; avoid corporate language, inflated benefits, and generic introductions.
- **Context:** start with current behavior and explain why it causes a problem: what breaks, becomes awkward, or creates work for the quant. Use a small example when useful; link prior decisions where they enter the reasoning.
- **Decision:** say what changes directly ("Use", "Introduce", "Move", "Require", or the component's new behavior), why, and the important tradeoff. First person is appropriate for the maintainer's stated reasoning; never invent personal history or experiments.
- **Consequences:** state costs, capabilities, and deferred work. One sentence can suffice, as in 0014; use bullets for distinct effects, including drawbacks. Do not repeat the decision as vague benefits.
- Let the problem determine length. Prefer connected paragraphs; reserve lists/code for material needing them. Explain meaningful alternatives without exhaustive matrices, implementation checklists, or feature-spec templates. Preserve candid technical reasoning and correct grammar; don't manufacture quirks. Compare the draft with its related ADR and remove padding.

## Computation and Strategy Contracts

- Keep `compute/` independent of trading concepts and concrete I/O.
- Preserve stable node equality/hashes; equivalent dependencies share computation. Pass the same source instance through dependent nodes. `SourceNode.factory()` returns the runner updated by `send()` (ADR 0012).
- `compute()` owns the source context; the source delegates resource management to its provider (ADR 0016). Explicitly close the generator when stopping consumption early.
- Strategy modules export a sink class as `__sink__`; backtesting constructs it with a source (ADR 0014).
- Rolling windows return newest first. The broker enters at the signal bar's close and evaluates exits on subsequent bars (ADR 0013). Prices/PnL use ticks, four per point for supported instruments. Preserve these conventions unless explicitly changed by the task.

## Code Style

Use four-space indentation, 88-character lines, double quotes, Google-style docstrings, `snake_case` functions/modules, and `PascalCase` classes. Satisfy strict Pyrefly; let Ruff organize imports. Follow `.editorconfig` (UTF-8, LF, final newlines, whitespace). Add `# SPDX-License-Identifier: Apache-2.0` to new source files.

- Prefer function composition, focused functions, guard clauses, and early returns. Roughly 25 executable lines is a review signal; extract cohesive helpers that improve readability.
- Inject dependencies through arguments or constructor/dataclass fields. Tests use the same points with small fakes/stubs. Only if injection is impractical and patching necessary, use scoped `unittest.mock.patch`, never pytest's `monkeypatch` fixture.
- Define collaborator contracts with `typing.Protocol` and structural duck typing; depend on the needed protocol, not a concrete implementation. Value objects/internal helpers need not have protocols. Use `@runtime_checkable` for runtime checks; see `compute/protocol.py` and `provider.py` under `src/ataraxia/`.
- Use dataclasses for structured data, preferably `@dataclass(frozen=True)` for values and node specifications; use `field(default_factory=...)` for per-instance containers/collaborators. Keep specifications hashable and execution state in callable runners; see `source.py` and `feature.py`.
- Avoid raw dictionaries for known records: use dataclasses or `TypedDict` when dictionary representation is required (`BrokerReturn`, `BacktestShardReturn`). Describe known key schemas with `TypedDict`; reserve explicitly typed `Mapping[K, V]`/`MutableMapping[K, V]` for dynamic keys such as nodes or dependency names.
- At library boundaries, translate expected low-level failures into contextual exceptions in `src/ataraxia/errors.py`. Derive from `AtaraxiaError`, retain an appropriate built-in base, and preserve causes: `raise DomainError("Useful context") from exc` (see `sort_graph`). Don't blanket-wrap programming errors or normal iteration termination. Document caller-handled domain errors in Google-style `Raises` sections.
- Node pattern: `deps()` names inputs, `factory()` supplies a runner, and runner `__call__` computes. Match dependency keys to runner parameters. Extract reusable calculations, as `SmaRunner` does with `sma`.
- Use modern typing: `T | None`, built-in generics, `type` aliases, parameterized protocols/classes, and `Literal` for closed sets (signal sides). Prefer `collections.abc` contracts (`Sequence`, `Mapping`, `Iterator`); require mutability only when needed.
- Use context managers for files/providers, preserving source/provider lifecycle delegation and cleanup on success/failure; use `pathlib.Path`.
- Keep console output in `src/ataraxia/cli.py`; libraries return values or raise domain errors.

### Preserve Type Precision

Type precision is part of correctness. Passing strict Pyrefly is necessary, but does not justify losing information about values or their relationships.

- Never resolve a mismatch by widening a meaningful type to `Any`, `object`, an unparameterized container, or a base type that discards the required contract. Do not remove annotations or add catch-all union members to make incompatible values fit. Existing broad types are debt, not precedent for spreading them.
- Model the actual contract. Introduce dataclasses, `TypedDict`s, protocols, or explicit unions of supported variants when needed. For reusable behavior, preserve input/output relationships with type parameters through producers, runners, consumers, and containers. A type parameter must be determined by a typed input or owning instance; an unconstrained return-only parameter does not establish safety.
- When annotations and behavior disagree, determine the intended supported cases and update the affected call chain coherently. Do not retain a false narrow annotation, silently drop supported behavior, or substitute a broad return type followed by caller-side runtime checks. Creating an appropriate type or separating distinct operations is preferable to erasing the distinction.
- Keep unavoidable untyped input at the external boundary. Validate or adapt it there into an explicit project contract before it enters application code. Do not expose that uncertainty through public result types. Casts, `TypeGuard`/`TypeIs`, ignores, and disabled diagnostics must not conceal a mismatch or replace a missing type model; narrowing predicates must actually establish their claimed contract.
- Verify both behavior and static guarantees. Run strict Pyrefly and inspect the affected signatures and inferred types; for generic or variant contracts, add focused type-checking cases that demonstrate precise results and rejection of invalid uses. Runtime tests and a green checker alone do not prove that useful type information was preserved.

## Testing Guidelines

Use pytest, `test_*.py` files, and `test_*` functions. Mirror source modules within unit/integration/acceptance directories where practical. Use fixtures for reusable inputs, `pytest.raises` for failures, `tmp_path` for filesystem tests, and `capsys` for CLI output. Cover changed behavior and relevant edges; maintain at least 80% coverage with branch measurement.

For relevant changes, cover dependency sharing and runner state; provider cleanup on exhaustion, error, and explicit generator closure; rolling-window ordering/warm-up; and broker timing preventing same-bar exits for new positions. Use integration tests for real strategy loading and acceptance tests for CLI output/artifacts.

For focused iteration: `uv run pytest test/unit/test_feature.py`. Default discovery covers `test/`; `make ci` also runs the example tests. Follow [Commands and Validation](#commands-and-validation) for required full checks.

## Commits and Pull Requests

Use Conventional Commits (Commitizen enforced), e.g. `test(compute): fix context manager exit method return value` or `docs: update architecture`. Keep changes focused. PRs explain the problem, resulting behavior, and validation, with relevant issue links.

Every agent-created commit must include a succinct body explaining **why** the change was needed, **what** changed, and **how** it was implemented. Use one short paragraph or up to three short bullets; include relevant validation briefly. Avoid repeating the subject, listing files, or narrating the work session.

External contributions are gated pending CLA setup; follow [CONTRIBUTING.md](CONTRIBUTING.md). Determine the PR base from explicit task instructions or repository metadata, consistent with contribution guidance.
