# Match selection investigation

## Question and evidence

Should repository guidance recommend `match` for suitable single-value
branching, and can pinned Ruff or another linter identify those opportunities
reliably?

The frozen seed sources show two different conversions:

- [`unsafe_case` before conversion](https://github.com/msitarz/ataraxia/blob/126b3807e3519fada2f85be03517ca651137ba8c/test/make/integration/test_worktree_removal.py#L32)
  used three independent string equality `if` statements; the reviewed result
  uses `match` in
  [`2ec5374`](https://github.com/msitarz/ataraxia/blob/2ec5374/test/make/integration/test_worktree_removal.py#L32).
  For its known distinct string cases, at most one action runs. The `main` case
  intentionally does nothing. Neither version has a catch-all: an unknown string
  reaches `reasons[condition]` and raises `KeyError`.
- [`arrange_changed_input` before conversion](https://github.com/msitarz/ataraxia/blob/89a7694564953ed1b2a26eedb075c804b3a21ba7/test/script/selection_inputs.py#L85)
  used an exclusive `if`/`elif`/`else` chain;
  [`a077245`](https://github.com/msitarz/ataraxia/blob/a077245/test/script/selection_inputs.py#L93)
  converted it to `match`. The shared destination mapping remains outside
  selection; its two keys share an arm. The fallback still raises `ValueError`
  for an unsupported name. These links identify the actual before and after,
  rather than attributing the already-converted `5d37d04` snapshot as the
  original arrangement.

## Options

| Option | Fit and evidence | Limit |
| --- | --- | --- |
| Pinned Ruff | The worktree setup ran locked `uv sync --locked` and offline check; `uv.lock` pins Ruff 0.16.8. Project lint selects `SIM`, including SIM116. The controlled Make probe reported SIM116 on three consecutive `if`/`elif` branches returning fixed strings and suggested a dictionary lookup. It reported nothing for the separate two independent `if` predicates in the same source. | SIM116 targets direct-return chains and a value lookup; it does not recommend `match` and cannot infer whether predicates are intended to be exclusive. It is relevant only when a pure fixed-value lookup is clearer. The configured rule set gives no general migration signal for the seed actions. |
| Another linter | No credible alternative with a verified rule for recommending Python `match` over behaviorally equivalent `if` branches was established for this question. | Adding or trialing another checker would require separate evidence and maintenance; no gap here justifies that work. |
| Guidance only | A reviewer can judge whether one subject intentionally selects one action, whether cases overlap, and what unmatched input must do. It applies to both seeds without claiming the tool proved the refactor. | It does not produce an automated warning; examples must remain limited so this does not become a conversion tutorial. |

Ruff evidence is local to the pinned installation and configured Make route.
The exact executed source is preserved as [probe.py.txt](probe.py.txt). To
reproduce, copy its contents verbatim to `match_selection_probe.py` at the
repository root, run `make lint-check ARGS=match_selection_probe.py`, and remove
the temporary `.py` copy after observing the result. The final run exited 2
with only the SIM116 diagnostic on `constant_return`; the independent
predicates produced no finding. The text artifact remains for the evidence
commit and can be retired during Work cleanup.
The rule's published scope is
[consecutive `if` statements with direct returns](https://docs.astral.sh/ruff/rules/if-else-block-instead-of-dict-lookup/).
Python documents that a `match` executes only the first matching case, and no
case runs when none matches; guards can continue to later cases
([match statements](https://docs.python.org/3/tutorial/controlflow.html#match-statements)).

## Conversion limits and recommendation

`match` fits when one stable subject selects one of several intentionally
exclusive literal or structural cases. Preserve a required rejection or
fallback, and keep shared setup and post-selection work outside the arms where
that is clearer. The worktree conversion is an example: its separate equality
checks are mutually exclusive for ordinary string inputs. The registry
conversion has an explicit unmatched-input error and grouped keys.

Independent predicates may both apply: for example, `if value > 0: mark()` and
`if value > threshold: alert()` can perform both actions. Converting them to
ordered cases would suppress one action when both predicates hold. Guard clauses
for early exits, unrelated predicates, and simple `if`/`else` expressions often
read more directly. A meaningful open-domain fallback does not establish a
finite domain. Prefer a dictionary when the operation is simply a mapping from
keys to fixed values. Preserve observable input and error behavior; do not
require preserving implementation order where it has no observable effect.

Recommendation: use concise guidance only. Ruff SIM116 is a useful narrow
signal for a different transformation, not a `match` policy; no alternative
checker is warranted by these examples. No tool or repository-wide rule change
is recommended. A small follow-up Work should carry the proposed wording below
to the existing owner of [engineering guidance](../../engineering.md), where
the maintainer can review it alongside the existing short `Literal` guidance.

> Use `match` when one value selects one of several distinct cases and only one
> case should run; preserve any required unmatched-input behavior. Keep
> independent `if` statements when multiple predicates may each apply, and use
> guard clauses for early exits or when they read more clearly. A dictionary
> lookup can suit a pure mapping from keys to fixed values. Do not infer a
> finite domain from listed cases or a default arm.

- **AC-1 DONE** A reviewable recommendation compares pinned Ruff, alternative
  tooling, and guidance-only options for suitable single-value branching,
  explains safe-conversion limits and false positives with examples, and states
  when `if` is preferable and whether a separate adoption Work is warranted.

  Validation: manually review the recommendation against the preserved seeds,
  pinned tool/version evidence and supported capabilities, representative
  positive and negative examples, and the existing engineering/testing guidance;
  run any project-tool experiments through Make and retain their outcomes.
