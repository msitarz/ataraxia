# Nested exception handling

Deliver engineering guidance forbidding nested exception handlers and automatic
lint prevention through the existing Ruff, Make and CI path where supported.
Both outcomes are required; an investigation or guidance alone does not complete
this Work. This Work separates the bounded tooling investigation from
policy/enforcement adoption.

The seed is the maintainer's
[comment on PR #328](https://github.com/msitarz/ataraxia/pull/328#discussion_r4271457416),
“add guidance to forbid nested try..except”. The preserved
[`_open_stable_lock` at reviewed head 47779e4](https://github.com/msitarz/ataraxia/blob/47779e4dbf3df31d0c4ebcffd9d074ba493ccff3/script/sandbox.py#L350-L393)
handles missing `lstat` input with an exclusive creation attempt that catches
`FileExistsError`, then validates and synchronizes the created descriptor under
`try`/`finally` cleanup. This Work does not change PR #328. Adoption checks the
then-integrated source; the permalink remains the historical seed.

At planning baseline `3e4f4b78fb81b07f8e1d28a35458da5dedb0aac3`,
[engineering guidance](../../engineering.md#code-style) already prefers
composition, guards, cohesive helpers and context managers and requires cause
preservation. It has no explicit nested-handler ban.
[Ruff configuration](../../../pyproject.toml) enables preview and SIM, but not
TRY or PLR1702. The [lockfile](../../../uv.lock) pins Ruff 0.16.8; the
dependency lower bound is not the installed-version evidence. Make runs blocking
Ruff lint plus separate advisory statement counts, and CI reuses the local
checks.

The proposed rule concerns lexical nesting within one execution scope: a
`try` with `except` or `except*` handlers must not contain another such `try`
anywhere in its body, handlers, `else` or `finally`, including through branches
and loops. A nested function or method starts a separate execution scope.
Async functions follow the same rule. Required `try`/`finally` and context
manager cleanup remain allowed, including nesting where either `try` has no
exception handler. Sequential handlers and branches inside one handler remain
allowed. Dynamic calls between cohesive helpers are allowed; extracting one
helper per line solely to evade lint is not an acceptable repair.

Preserve the seed's operation-specific error scopes: only the first `lstat`
failure selects creation; only exclusive `os.open` losing the race catches
`FileExistsError`. Validation, fsync and subsequent `lstat` failures propagate.
Created descriptors close once on success or failure; the returned descriptor
stays open and closes if its validation fails. Preserve explicit causes, bare
reraises and intentional `from None` when moving handlers. Combining catches
around a larger region can silently change these contracts.

A proposed cohesive extraction is a helper owning exclusive creation and its
temporary descriptor: catch `FileExistsError` only around `os.open`, return on
that race, then validate/fsync in a separate `try`/`finally` that closes the
created descriptor. The caller invokes that helper from its missing-file
handler after the reserved-name guard, then repeats `lstat` there. The helper's
cleanup remains required; errors it propagates must not acquire a new catch or
translation. This illustrates shape and ownership, not an approved patch.

Use two serial leaves so the uncertain tool decision and the eventual policy
change each fit a short review:

- TODO [Enforcement investigation](investigate/README.md): establish a supported
  mechanism and report a concrete choice if Ruff cannot enforce the rule.
- TODO [Guidance and enforcement adoption](adopt/README.md): after independent
  review of that mechanism and any required maintainer steering, deliver both
  lasting guidance and prevention with only necessary violation repairs.

No new dependency, custom scanner, broad nesting threshold, general lint
framework or repository-wide refactor is automatically authorized. A capability
gap pauses adoption and requires maintainer choice: wait for a supported Ruff
rule or explicitly authorize a narrowly scoped alternative. A large violation
inventory requires a reviewed bounded split before implementation. Neither
choice changes the required outcome or permits docs-only completion.

- **AC-1 TODO** Both serial outcomes are independently reviewed and integrated:
  engineering guidance defines the intended ban and a supported automatic check
  prevents it at the normal Make/CI boundary, with preserved exception and
  resource behavior and no outstanding enforcement gap.

  Validation: review child delivery evidence and the lasting engineering,
  configuration and command owners; observe prohibited examples fail and allowed
  examples pass through the adopted route. Review affected behavior evidence and
  scope before parent completion. Run Make documentation and acceptance checks.
