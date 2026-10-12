# Commit staged changes with a formatted body

Add `make commit SUBJECT=... BODY=...` for already-staged changes. Preserve the
single-line subject unchanged, allow an omitted/empty body, and format body
prose before invoking ordinary `git commit` with every installed hook enabled.
The existing Conventional Commit hook validates the subject; this helper does
not invent another subject policy. Reject a missing or multiline subject before
committing. Implement only after the maintainer merges this standalone plan,
before subsequent Work-tree delivery.

## Reuse and formatting boundary

[CONTRIBUTING](../../../CONTRIBUTING.md#commits-and-pull-requests) and
[the existing checker](../../../script/check_commit_message.py) already own body
separation, `BODY_WIDTH=72`, eight-column tab stops, and the allowance for
standalone unbreakable tokens with indentation, bullet or trailer prefixes.
Reuse that policy at its owner rather than copy constants/recognition rules or
relax the hook. Share a small policy helper only where necessary; retain checker
behavior and existing tests. No Markdown parser or formatting framework is
needed.

Treat unmarked body text as prose paragraphs separated by blank lines. Reflow
within each paragraph at 72 columns, counting indentation and prefixes; retain
paragraph boundaries and word order. Preserve bullet markers (`-`, `*`, `+`,
numbered `1.`/`1)`) and wrap their contiguous prose continuations with hanging
indentation. Preserve unbreakable tokens intact, placing a long URL/token on
its own line with any allowed prefix rather than splitting it or keeping
adjacent prose on an over-width line.

Literal commands require an explicit boundary: preserve lines inside a
backtick/tilde fenced block, and lines indented by four spaces or a tab outside
an active bullet continuation. Preserve literal bytes/line breaks; do not
reflow shell commands or insert continuation escapes. The small formatter
recognizes only these boundaries, not Markdown nesting or shell syntax.
Unmarked lines are prose; usage guidance must show how to mark literal commands.
A literal line rejected by the existing wrapping policy, such as an over-width
multiword command, remains unchanged and fails visibly before a commit is
created. Callers must supply an
already compliant command layout; the helper must not silently corrupt it to
make the hook pass. Subject/body separation is one blank line when body exists.

## Literal transport and commit scope

The current Make `_SHELL_VALUE` handles apostrophes at the shell boundary, but
ordinary `$(SUBJECT)`/`$(BODY)` and recursive export can evaluate Make input
before that boundary. Capture raw input without recursive Make evaluation
(for example with `$(value ...)` and controlled nonrecursive transport), avoid
inline shell interpolation, and pass Git arguments as a Python argument list.
Subject/body apostrophes, quotes, backticks, dollar signs and Make-looking
expressions must arrive as literal data, including multiline BODY. Existing
shell quoting remains the caller's responsibility before Make receives values;
document one safe usage form. Do not evaluate message text with shell, `eval`,
recursive Make expansion or command substitution.

Run Git in the caller's worktree against its existing index. Do not auto-stage,
amend, allow empty commits, publish, change Git/hook configuration or bypass
hooks. Preserve normal Git/hook diagnostics and nonzero failure; no readiness
or success claim after refusal. Hook failure must not advance HEAD; ordinary
hook side effects are not rolled back by this helper. No dependencies or general
Git wrapper are in scope. Add minimal Make help/CONTRIBUTING usage and precise
script types under existing [engineering conventions](../../engineering.md).

- **AC-1 TODO** Given prose paragraphs, bullets/continuations, long tokens and
  explicit literal blocks, formatting follows the existing 72-column policy,
  preserves subject/paragraphs/tokens and literal text, and refuses incompatible
  literal widths without a commit or command corruption. Omitted BODY produces
  a subject-only message.

  Validation: criterion-marked formatter tests compare independent expected
  messages for the stated cases, including exactly 72/over-width, tab columns,
  long tokens with prefixes and verbatim commands. Reuse existing checker-policy
  tests and inspect unchanged hook behavior; no fixture-schema duplication or
  exhaustive Markdown parsing suite.
- **AC-2 TODO** Given raw SUBJECT/BODY containing quoting and Make/shell-looking
  text, the Make route forwards literal data safely and commits only staged
  changes through ordinary Git/hooks, or fails visibly with HEAD unchanged.

  Validation: focused Make routing tests cover literal dollars, apostrophes,
  quotes, backticks, multiline input and `$(shell ...)`/`${...}` text, asserting
  exact received message data and absence of execution sentinel effects. Reuse
  [Make helpers](../../../test/make/support.py) and
  [disposable Git/process helpers](../../../test/script/commit_message_support.py)
  for real successful commits, an unstaged-file preservation case and hook
  refusal, including Conventional Commit rejection. Shims prove routing only;
  inspect stored messages and refs for real commit outcomes. Bound subprocess
  tests, run affected lint/type/doc/ac checks, and independently review minimal
  usage guidance under [testing](../../testing.md) and
  [integration guidance](../../testing-integration.md).
