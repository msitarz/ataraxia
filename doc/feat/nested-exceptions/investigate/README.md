# Nested exception enforcement investigation

Which supported lint mechanism can enforce the exact proposed rule in the
[parent contract](../README.md) without rejecting ordinary branching or required
cleanup? Produce a bounded recommendation before adoption; do not enable lint,
change engineering policy or repair production code here.

Inspect Ruff 0.16.8 as owned by `uv.lock`, its selected rules and supported
settings, then compare concrete diagnostics against the parent seed and small
counterexamples. Official documentation describes
[PLR1702](https://docs.astral.sh/ruff/rules/too-many-nested-blocks/)
as general block nesting with a default allowance of five;
[TRY300](https://docs.astral.sh/ruff/rules/try-consider-else/)
addresses returns in `try`, and
[TRY301](https://docs.astral.sh/ruff/rules/raise-within-try/)
addresses explicitly raising exceptions caught by the same `try`. These
documented purposes do not establish exact enforcement of the requested ban.
Current documentation is not evidence of the pinned version's observed behavior;
see the [pinned-version comparison](comparison.md) for Make observations.

Compare any promising pinned Ruff configuration with a minimal alternative
only if necessary. A targeted checker is a candidate requiring explicit
maintainer authorization, not a preapproved implementation. Guidance alone may
be compared to explain its enforcement gap but cannot satisfy the parent.
Setting universal maximum nesting to one or enabling unrelated TRY rules does
not count as precise prevention.

Use this shared matrix for the recommendation and adoption examples:

| Arrangement within one execution scope | Required result |
| --------------------------------------------------------- | ----------------------------------- |
| Handler-bearing `try` inside another's body | Reject |
| Handler-bearing `try` inside an `except`, `else` or `finally` | Reject |
| Nested handlers catching different exception types/scopes | Reject; preserve scopes in repair |
| Two sequential `try`/`except` statements | Allow |
| One `try`/`except` with branches or loops inside it | Allow |
| Nested `try`/`finally` cleanup or context managers | Allow when either try has no handler |
| A separate nested function with its own single handler | Allow across that lexical boundary |
| Async functions and supported `except*` nesting | Apply the same lexical rule |

Execute project-tool experiments only through Make. `make lint-check ARGS=paths`
accepts paths, not arbitrary Ruff options. A temporary local Ruff configuration
that extends the repository configuration allows candidate settings to be
observed through that existing route. If that route proves insufficient, define
the smallest Make extension under owner review before using it. Record exact
locked version, candidate settings, commands, exit status, diagnostics and
limitations in a small comparison linked from this README while it exists.
Inspect the relevant source/configuration and then-integrated violations to
bound adoption. Testing a candidate is not permission to adopt it.

See [Pinned Ruff comparison](comparison.md) for the observed matrix, source
inventory and recommendation.

- **AC-1 DONE** A reviewable comparison identifies what the pinned Ruff version
  can and cannot enforce using observed seed/matrix diagnostics, recommends a
  supported precise mechanism, and bounds the necessary violation repairs. If no
  Ruff mechanism fits, it reports the specific gap and maintainer choice between
  waiting for supported Ruff enforcement and explicitly authorizing a minimal
  alternative; adoption remains blocked until that choice is made and supported.

  Validation: independently review the comparison, locked-version and official
  source evidence, candidate settings and observed Make experiments against
  every matrix row. Distinguish exact enforcement from broader complexity
  checks; inspect false positives, missed cases, cleanup/cause preservation and
  the repair inventory. Run Make documentation and acceptance checks. This
  Investigation may finish with a reviewed capability-gap finding; the parent
  cannot finish on that finding alone.
