# Repository Guidelines

## Project Structure & Module Organization

Ataraxia is a pre-alpha orchestrator for bar-by-bar trading backtests. Python code lives in `src/ataraxia/`: `compute/` implements the computation graph and loop; sibling modules handle sources, providers, features, brokerage, backtesting, and the CLI. Tests are grouped under `test/unit/`, `test/integration/`, and `test/acceptance/`. `example/` contains a crossover strategy and its tests; `sample/` contains synthetic CSV data. Read `doc/architecture.md` and relevant records in `doc/adr/` before changing architectural boundaries.

Current execution is local, sequential, and single-source. Parallel execution, multi-source synchronization, and immutable artifact storage are planned. Verify implementation status in code before treating architecture or feature documents as existing behavior.

## Build, Test, and Development Commands

Use Python 3.14+, `uv`, and `make`.

- `make setup`: synchronize dependencies and install prek pre-commit and commit-message hooks.
- `uv sync --frozen --group dev`: install locked dependencies without installing Git hooks, as CI does.
- `make lint`: run Ruff with automatic fixes.
- `make format`: format Python files with Ruff.
- `make typecheck`: run strict Pyrefly checks on `src/`.
- `make test`: run pytest with branch coverage.
- `make ci`: check lint, formatting, types, and test coverage before submitting changes.
- `uv run pytest example/`: run example tests separately from default test discovery.
- `uv audit --frozen --preview-features audit`: audit dependencies, as CI does separately from `make ci`.
- `uv build`: build distribution artifacts using the configured `uv_build` backend.

When changing dependencies, update and include `uv.lock`. Use the Makefile and CI workflow to verify executable commands; `CONTRIBUTING.md` currently references a nonexistent `make check` target.

Run the sample strategy locally:

```sh
uv run ataraxia --sink example/crossover.py --shards-dir sample --output results.json
```

## Ubiquitous Language

Use a shared vocabulary whose meaning stays consistent within the relevant domain or module. [doc/ubiquitous-language.md](doc/ubiquitous-language.md) is the single source of truth for shared domain terms. AI-generated specifications and code must use the project's established concepts and contracts.

- Before writing a slice, ADR, or implementation, read the relevant terms in `doc/ubiquitous-language.md`, then inspect their definitions in code, tests, and applicable ADRs. Distinguish current implementation from intended changes; surface discrepancies that affect the task.
- Use the same terms in discussions, specifications, identifiers, docstrings, tests, and examples. Reuse existing abstractions when their meaning fits. When delegating work, include the relevant vocabulary and contract references so agents share the same context.
- Keep distinct concepts distinct. A `Provider` supplies input; a `Source` exposes it to the computation graph; a `Runner` is the callable that executes a node. A runner is not an executor worker. Use "feature slice" for a delivery increment when "feature" could be confused with a composable calculation. Qualify terms at real boundaries and explain mappings where meanings differ.
- Resolve ambiguity using the request and repository context first. If plausible meanings would produce materially different behavior and intent remains unclear, present concrete interpretations to the user before implementing the affected behavior. Do not silently invent domain rules; routine naming choices consistent with established meanings do not require confirmation.
- Maintain shared definitions in `doc/ubiquitous-language.md` and feature-local rules in the relevant slice. Describe a concept's responsibility, relationships, and significant units or lifecycle rules where needed. Refine definitions as understanding grows, update affected code, tests, and docs together, and use the ADR workflow for architectural changes. Preserve historical ADRs and link to the glossary rather than duplicating it in other documents.
- Verify meaning through observable examples and tests, including timing, units, state transitions, and failure behavior where relevant. Matching terminology alone does not establish correctness; review whether generated code implements the agreed behavior and preserves module boundaries.

Background: [Thoughtworks on ubiquitous language](https://www.thoughtworks.com/insights/blog/evolutionary-architecture/domain-driven-design-in-10-minutes-part-one), [Fowler and Joshi on LLMs and abstractions](https://martinfowler.com/articles/convo-llm-abstractions.html), and [Daniel Schleicher on resolving ambiguity with AI](https://www.danielschleicher.com/software/engineering,/ai,/spec-driven/development/2026/01/04/removing-ambiguity-with-spec-driven-development.html).

## Writing Feature Slices

Write feature-slice specifications in `doc/feature/`. Keep each document proportional to the change; use short prose and examples without requiring a user-story formula or Gherkin syntax.

- Lead with the problem, the current behavior verified in code, and the observable outcome for a user or library caller. Mark the status explicitly, such as proposed, in progress, or validated, and link relevant issues and ADRs.
- Scope a small, usable increment through the components needed to deliver that outcome. Split larger features by supported scenarios or capabilities. State non-goals and dependencies; identify preparatory refactors and technical experiments separately. Include the correctness, failure handling, and tests needed for the supported scenario within the slice.
- Describe acceptance criteria as concrete examples: relevant preconditions and inputs, an action, and expected outputs or side effects. Cover the main behavior, significant boundary/failure cases, and existing behavior that must remain intact. Express intent through observable contracts so tests can survive implementation changes.
- Separate required contracts from provisional design notes. Specify affected interfaces, ordering, compatibility, and resource ownership where relevant. Sketch only enough implementation detail to explain feasibility and consequential tradeoffs; link architectural decisions rather than duplicating them. Leave internal design choices open where they do not affect the contract.
- When planning or implementing a slice, ensure every relevant architectural decision is covered by an ADR using the workflow below. Link the applicable records from the slice, including decisions discovered during implementation.
- Name important assumptions and open questions. When uncertainty could invalidate the approach, propose a bounded experiment with an expected result and evidence that would challenge it. Record what was learned and revise the plan; distinguish an experiment's findings from a completed feature.
- Plan short implementation steps with a working path and feedback early. Pair behavior changes with their tests throughout the plan, and keep existing behavior working between steps. Refine the scenario list as new cases emerge; make changes to agreed scope or contracts explicit.
- Separate the validation plan from recorded results. Say which focused, integration, or CLI checks demonstrate acceptance, using the appropriate test boundary for each. For performance claims, specify the baseline, representative workload, measurement method, and success criterion. Mark a slice validated only after its acceptance criteria and required repository checks pass; record evidence and limitations.

For example, a parallel-backtest slice can specify that the same strategy and shards produce identical ordered results with one or two workers, and that a shard failure preserves an existing output file. These are observable acceptance examples; executor classes and scheduling helpers belong in design notes.

Background: [Thoughtworks on vertical slicing](https://www.thoughtworks.com/en-au/insights/e-books/modern-data-engineering-playbook/delivery-planning-principles), [Martin Fowler on outcomes and evolving plans](https://martinfowler.com/bliki/FeatureDevotion.html), [Kent Beck on behavioral scenarios and incremental tests](https://newsletter.kentbeck.com/p/canon-tdd), and [Dave Farley on intent and acceptance tests](https://www.davefarley.net/?page_id=50).

## Architecture Decision Records

- Before writing an ADR, search `doc/adr/` for the problem and related decisions, read relevant records, and follow amendment or supersession links to the current decision. If an existing ADR already covers the intended approach, reference it rather than creating a duplicate.
- Create an ADR whenever a relevant architectural decision is not already recorded, such as a choice about module boundaries, execution models, resource ownership, or persistent contracts. Record the decision before implementing the affected design; revisit this check when implementation reveals new architectural choices.
- Use the next unused sequential number and the existing `NNNN-kebab-case-title.md` naming convention. Follow the repository format: `# N. Title`, `Date: YYYY-MM-DD`, and `Status`, `Context`, `Decision`, and `Consequences` sections. Explain the problem, relevant alternatives and tradeoffs, chosen approach, and consequences. Use `Proposed` while a decision is unsettled and `Accepted` once decided.
- To change an accepted decision, create a new ADR and preserve the earlier record's context, decision, and consequences. For a partial change, add `Amends [N. Title](NNNN-title.md)` in the new record's Status section; once accepted, add the reciprocal `Amended by [M. Title](MMMM-title.md)` to the earlier record. Follow ADRs 0010 and 0011 as examples, and make clear which parts still apply.
- For a replacement, use `Supersedes [N. Title](NNNN-title.md)` in the new record and, once accepted, change the earlier record's status to `Superseded by [M. Title](MMMM-title.md)`, following [adr-tools conventions](https://github.com/npryce/adr-tools). Use relative Markdown links between ADRs. Update the feature slice's links and `doc/architecture.md` to reflect the resulting decision and implementation status.

### ADR Writing Style

Match the maintainer's direct, practical voice. Before drafting, reread the closest related ADR; use ADR 0014 for a small convention, 0012 for a tradeoff, and 0016 for a lifecycle change as style references.

- Use a short, sentence-case title naming the actual choice. Write plain, conversational English with concrete code and domain terms. Contractions and occasional blunt sentences are natural; avoid corporate language, inflated benefits, and generic architecture introductions.
- In Context, start with what the system does today and walk through why it causes a problem. Connect cause to effect: what breaks, becomes awkward, or creates work for the quant. Use a small code example or a concrete scenario when it makes the mechanism easier to see. Link prior ADRs where their decisions enter the reasoning.
- In Decision, say what changes directly: "Use", "Introduce", "Move", "Require", or the named component followed by its new behavior. Include the reason and the important tradeoff in ordinary prose. Use first person for the maintainer's stated reasoning where natural, without inventing personal history or experiments.
- In Consequences, state what the choice costs, enables, or leaves for later. A single sentence is enough for a small decision, as in ADR 0014. Use bullets for several distinct effects, including drawbacks. Avoid repeating the decision as a list of vague benefits.
- Let the problem determine the length. Prefer connected paragraphs under the existing headings; reserve code blocks and lists for material that needs them. Explain alternatives that mattered without adding an exhaustive options matrix, implementation checklist, or feature-spec template.
- Preserve the candid reasoning and technical specificity, while keeping spelling and grammar correct. Do not manufacture quirks or repeat catchphrases to imitate the voice. Read the draft beside its related ADR and remove any padding that the decision does not need.

## Computation and Strategy Contracts

- Keep `compute/` independent of trading concepts and concrete I/O implementations.
- Preserve stable node equality and hashes throughout execution; equivalent dependency specifications share computation. Pass the same source instance through dependent nodes. `SourceNode.factory()` must return the runner updated by `send()` (ADR 0012).
- `compute()` owns the source context; the source delegates resource management to its provider (ADR 0016). Callers that stop consuming the compute generator early should explicitly close it.
- Strategy modules export a sink class through `__sink__`; backtesting constructs it with a source instance (ADR 0014).
- Rolling windows return newest values first. The current broker enters positions at the signal bar's close and begins evaluating their exits on subsequent bars (ADR 0013). Prices and PnL use ticks, with four ticks per point for supported instruments. Preserve these conventions unless the task explicitly changes them.

## Code style

Use four-space Python indentation, 88-character lines, double quotes, and Google-style docstrings. Follow existing `snake_case` function/module names and `PascalCase` classes. Keep code compatible with strict Pyrefly checking and let Ruff organize imports. Follow `.editorconfig` for UTF-8, LF endings, final newlines, and whitespace. Add `# SPDX-License-Identifier: Apache-2.0` to new source files.

- Prefer function composition over nested control flow. Keep functions and methods focused, and use guard clauses and early returns to keep nesting shallow. Treat roughly 25 lines of executable code as a review signal; extract helpers when they represent a cohesive operation or improve readability.
- Inject dependencies through function arguments or constructor/dataclass fields instead of monkey patching globals or collaborators. Use the same injection points in tests with small fakes or stubs implementing the required behavior. Only when injection is impractical and patching is absolutely necessary, use `unittest.mock.patch` in a scoped context manager instead of pytest's `monkeypatch` fixture.
- Define collaborator interfaces with `typing.Protocol` and structural duck typing; callers should depend on the required protocol rather than a concrete implementation. Value objects and internal helpers do not all need protocols. Use `@runtime_checkable` when runtime protocol checks are needed, following `src/ataraxia/compute/protocol.py` and `src/ataraxia/provider.py`.
- Describe structured data with dataclasses. Prefer `@dataclass(frozen=True)` for value objects and computable node specifications, and use `field(default_factory=...)` for per-instance containers or collaborators. Keep node specifications hashable; put execution state in their callable runners, following `src/ataraxia/source.py` and `src/ataraxia/feature.py`.
- Avoid raw dictionaries for records with known fields. Prefer dataclasses, or `TypedDict` when a dictionary representation is required, as in `BrokerReturn` and `BacktestShardReturn`. Reserve general mappings for truly dynamic keys, such as computable graph nodes or dependency names. Prefer `TypedDict` wherever the key schema can be described; for genuinely arbitrary keys, use explicitly typed `Mapping[K, V]` or `MutableMapping[K, V]` contracts.
- Translate expected low-level failures at library boundaries into contextual domain exceptions defined in `src/ataraxia/errors.py`. Derive new domain exceptions from `AtaraxiaError`, retain a relevant built-in exception base where appropriate, and preserve the cause with `raise DomainError("Useful context") from exc`, following `sort_graph` in `src/ataraxia/compute/graph.py`. Avoid blanket wrapping of programming errors or normal iteration termination. Document domain errors callers are expected to handle in a Google-style `Raises` section.
- Follow the computation node pattern: `deps()` declares named inputs, `factory()` supplies a runner, and the runner's `__call__` performs computation. Match dependency keys to runner parameter names. Extract reusable calculations into standalone functions, as `SmaRunner` does with `sma`.
- Use modern Python typing: `T | None`, built-in generics, `type` aliases, and parameterized protocols/classes. Prefer `collections.abc` interfaces such as `Sequence`, `Mapping`, and `Iterator` in contracts; require mutable interfaces only when mutation is needed. Use `Literal` for closed sets of values, as with signal sides.
- Use context managers for files and providers so resources close on success and failure. Follow the source/provider context-manager delegation pattern, and use `pathlib.Path` for filesystem paths.
- Keep console output in `src/ataraxia/cli.py`; library functions return values or raise domain errors. Use pytest fixtures for reusable test inputs, `pytest.raises` for error behavior, `tmp_path` for filesystem tests, and `capsys` for CLI output assertions.

## Testing Guidelines

Use pytest with `test_*.py` files and `test_*` functions. Place tests in the appropriate unit, integration, or acceptance directory, mirroring source modules where practical. Cover changed behavior and relevant edge cases. Coverage must remain at least 80%, with branch measurement enabled. For focused iteration, run `uv run pytest test/unit/test_feature.py`. Default discovery covers `test/`; example tests require a separate invocation.

For relevant changes, cover dependency sharing and runner state, provider cleanup on exhaustion/error/explicit generator closure, rolling-window ordering and warm-up behavior, and broker timing that prevents same-bar exits for newly opened positions. Use integration tests for real strategy loading and acceptance tests for CLI output and artifacts.

For code changes, run focused tests during development, then `make ci` and `uv run pytest example/`. CI additionally performs frozen dependency synchronization and package auditing. Report checks that could not run.

## Commit & Pull Request Guidelines

Use Conventional Commits, enforced by Commitizen: examples include `test(compute): fix context manager exit method return value` and `docs: update architecture`. Keep changes focused. Describe the problem, resulting behavior, and validation in PRs; link relevant issues. Open an issue before non-trivial architectural work. Follow the Architecture Decision Records workflow for architectural changes.

External contributions are currently gated pending CLA setup. Before opening a PR, determine the intended base from repository metadata or explicit task instructions; ask only if it remains ambiguous. `CONTRIBUTING.md` names `main`, while CI's push trigger names `master`; the trigger alone does not establish the intended PR base.
