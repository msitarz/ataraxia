# Adopt focused exception lint

Enable precisely Ruff
[TRY300](https://docs.astral.sh/ruff/rules/try-consider-else/),
[TRY301](https://docs.astral.sh/ruff/rules/raise-within-try/) and
[PLW0717](https://docs.astral.sh/ruff/rules/too-many-statements-in-try-clause/)
through the existing blocking Make/CI lint path. These checks encourage success
returns outside the protected `try`, prevent explicit raises caught by that
same `try`, and limit statements in a `try` clause. Use Ruff's default maximum
of five statements; existing preview mode supports PLW0717.

At inspected baseline `5c431a86d22af7f6328042faf38b508f94b53023`,
[configuration](../../../pyproject.toml) enables preview but none of these
rules; [uv.lock](../../../uv.lock) pins Ruff 0.16.8.
[Make](../../../Makefile) already runs configured Ruff with full and focused
paths, and [CI](../../../.github/workflows/ci.yml) reaches it through
`ci-check` and `verify-check`. Adoption should require configuration changes
and only necessary bounded repairs, rather than another command path.

Source reading identifies likely repairs in `BarProvider.__next__`'s success
return and the explicit raise used to obtain a traceback in the SourceNode
lifecycle test. This is a provisional inventory, not observed Ruff diagnostics;
confirm the locked tool's actual findings at execution, including scripts and
tests. Preserve row parsing and `Bar.from_map` inside their error translation
scope when moving the return. Preserve causes, exhaustion propagation and file
closure, and retain exact exception/traceback forwarding in the lifecycle test.
Other repairs must likewise preserve operation-specific catch scopes,
propagation, explicit causes, bare reraises, intentional `from None` and
cleanup/resource ownership. Extract only cohesive helpers needed for readable
repairs. Stop and report if the complete adoption exceeds a five-minute review.

This is a standalone leaf with no dependency on the delivered
[nested-exception guidance](../../engineering.md#code-style). These three rules
do not enforce its exact lexical nesting ban.
Do not rewrite PR #328, add other TRY/PL selections, a custom checker or new
dependency, or grandfather findings with blanket suppressions. Any lasting
guidance belongs in the existing engineering owner as at most one concise
sentence or paragraph, without a tutorial or historical links.

- **AC-1 TODO** The configuration adds exactly TRY300, TRY301 and PLW0717,
  retains preview and the default five-statement limit, and enforces them as
  blocking checks through ordinary full/focused lint and the existing CI route.
  The repository passes lint after necessary repairs.

  Validation: independently review configuration, Make and CI wiring; run
  `make lint-check` and focused lint on affected paths. Reuse the existing
  `test/make/integration/test_routing.py` and `test_execution.py` coverage; add
  criterion-marked integration coverage only for a missing configuration or
  routing obligation. Run relevant tests through Make. Do not retain tests of
  upstream rule semantics; if one-time adoption probes are needed, preserve
  exact revision, command, inputs, configuration and observed results in a
  source report/artifact and retained verification Git history before removing
  them under [test ownership](../../test-ownership.md).

- **AC-2 TODO** Necessary repairs preserve observable success, failure and
  resource behavior at each affected boundary, including the provider's
  contextual errors/causes and SourceNode's exact lifecycle forwarding.

  Validation: independently review the actual findings and repairs. Reuse
  focused provider, graph, script and lifecycle tests as applicable; mark tests
  that cover this criterion and add behavior regressions only for an uncovered
  contract affected by an actual repair. Run selected tests and affected type
  checks through Make. If a boundary needs no repair, inspect the inventory
  rather than adding tests for it. Review any lasting guidance for scope and
  accuracy; run `make doc-check` and
  `make ac-check WORK=doc/feat/exception-lint/README.md`.
