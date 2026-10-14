# Literal selection guidance

PROPOSED adoption scope: promote the reviewed Literal-selection recommendation
into
[engineering's type-precision section](../../engineering.md#preserve-type-precision).
This contract preserves the chosen direction for later guidance adoption; it
does not establish current engineering policy or authorize execution of that
Work. The complete guidance change and compact examples should fit one review of
about five minutes.

The dependency is the independently reviewed
[Investigation at `811c4de`](https://github.com/msitarz/ataraxia/blob/811c4de0943b2faf9877ffd4471125fbd77bf92c/doc/feat/literal-selection/investigation.md).
Its retained Git sources and observed probes used Python 3.14.8, Pyrefly 1.3.1
and Ruff 0.16.8. Alias annotations reject invalid typed uses but do not validate
runtime input. Explicit matched narrowing repeats alias members, and its
completeness was not proved. A flat PEP 695 Literal alias with
`get_args(Alias.__value__)` and a per-domain `TypeIs` predicate demonstrated
precise narrowing and runtime membership with one member inventory. A predicate
must actually establish its claimed contract; this result does not justify
mandatory reflection or a generic validation framework for every domain.

Engineering already requires Literal for closed sets, truthful type models and
external-boundary adaptation. The remaining gap is how to identify intentionally
finite string domains, choose their runtime representation and preserve member
inventory ownership. Review and integrate the existing section as a whole;
consolidate overlapping type-precision explanations and link to
[testing guidance](../../testing.md) for test ownership. Reconcile with the
[validated-core plan](../validated-core/README.md)'s consumed-boundary
validation direction without duplicating it or inventing a merge prerequisite.
Match selection and algebraic-data-type representation remain separately owned
questions.

The future guidance must require intentional domain contracts, separate aliases
when meanings differ, and validation of actual `str` input at the consumed
external boundary before narrowing to the correct domain. Preserve runtime
rejection of unsupported values and meaningful consumer/caller types without
casts, broadening or diagnostic suppression. An annotation or current match
arms, test parameters and observed values do not prove domain closure.

Compare concrete per-domain patterns in one compact illustrative example: a
validator accepting `str` returns its domain alias or rejects an unsupported
value; a consumer accepts that alias. Show two distinct domains, rejection of
non-string external input and a value belonging only to the other domain, and
static rejection of an open string passed directly to the consumer. Compare an
alias-derived membership `TypeIs` predicate against explicit matched narrowing
where cases perform distinct actions. Prefer one authoritative member inventory;
justify any action-case enumeration and check it covers all supported behavior
rather than adding parallel sets or registries. Do not merely assert lexical
aliases: demonstrate runtime validation and the narrow result's typed use.
Public signatures, accepted/rejected inputs and observable results suffice;
these examples do not create production APIs or templates.

Explain that Enum owns a member inventory when identity or behavior is useful,
but changes the runtime API to members and requires wire-string conversion.
Keep `str` for open defaults, paths, hashes, plugin keys, extensions and
overlapping classifications. Include a meaningful fallback that accepts a
future value and an open dynamic-domain counterexample. Configured Ruff did not
identify domains; pinned Pyrefly's incomplete Literal match produced a hidden
warning and exit 0. The mypy/Pyright exhaustiveness comparison was documented,
not locally executed. These findings do not warrant a general lint rule,
checker migration or a requirement that every match be exhaustive.

Scope is guidance only: no codebase migration, dependencies, tool rules,
checker changes, production templates or tests of upstream behavior. If example
review discovers an implementation defect, report it for a separately approved,
bounded Work rather than expanding this delivery.

- **AC-1 DONE** The existing engineering owner integrates intentional finite
  string domains, truthful consumed-boundary validation, distinct domain aliases
  and one authoritative member inventory or justified complete action-case
  enumeration. A compact comparison demonstrates actual runtime rejection and
  precise consumer typing for alias-derived predicates and explicit narrowing,
  while retaining the existing type-precision and boundary requirements.

  Validation: independently review the whole affected section and illustrative
  signatures against the frozen Investigation. Walk through valid members,
  non-string input, cross-domain and unknown values, direct open-string calls,
  predicate soundness and complete supported action behavior. Where useful,
  type-check the concrete snippets through existing Make targets and retain the
  observed outcomes; annotations alone are insufficient. Run `make doc-format`,
  `make doc-check` and `make ac-check` for this Work.

- **AC-2 DONE** The same compact guidance distinguishes useful Enum identity
  and wire conversion from ordinary finite strings and preserves open-domain
  defaults, paths, hashes, plugins, extensions and overlapping classifications.
  It states the observed tooling limits accurately and integrates existing
  guidance without adding policy copies or enforcement outside this scope.

  Validation: independently review a future-value fallback and dynamic-domain
  counterexample, Enum input/output compatibility and inventory ownership.
  Compare tooling claims to the frozen report, distinguishing executed probes
  from documentation-only alternatives. Review related type-precision,
  testing and consumed-boundary guidance for consistency and duplication, and
  confirm the complete leaf remains reviewable in about five minutes. Run
  documentation and acceptance checks through Make.
