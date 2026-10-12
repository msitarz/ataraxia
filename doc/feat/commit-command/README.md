# Commit staged changes with a rumdl-formatted body

Add `make commit SUBJECT=... BODY=...` for already-staged changes. Preserve the
single-line subject unchanged, allow an omitted/empty body, and format only the
Make-provided body with existing rumdl before ordinary `git commit` with every
installed hook enabled. The Conventional Commit hook validates the subject;
reject a missing or multiline subject before committing. Implement after the
maintainer merges this standalone plan, before subsequent Work-tree delivery.

## Existing formatter and checker boundaries

Use pinned rumdl's stdin formatter with `--no-config --enable MD013` and inline
settings for reflow, width from `BODY_WIDTH` in
[the existing checker](../../../script/check_commit_message.py), and disabled
code-block/code-span/heading/table reflow. The exercised configuration isolates
body formatting from repository Markdown settings; `--no-config` defaults fence
tools to disabled. Do not pass `--no-code-block-tools`, which is incompatible
with stdin mode. No dependency, custom prose parser or shared-core refactor is
needed. Rumdl startup/format failure must remain visible and prevent commit.

The rumdl 0.2.79 probe preserved paragraphs, bullet continuations and long
unbreakable tokens, and normalized tabs in ordinary prose. Adopt those native
formatting boundaries. Mark literal commands with fences or code indentation;
rumdl preserves their command text and line breaks. Unmarked commands are prose
and may reflow. Literal lines rejected by the current checker, including an
over-width multiword command, remain unchanged and fail visibly without a
commit. A marked 72-column command is accepted; its 73-column counterpart is
preserved and refused. Do not insert shell continuation escapes to force fit.

Dedicated Git trailer preservation is outside scope. In the probe, a long
`Signed-off-by: <email>` line was split into label and token lines and lost Git
trailer recognition even though the width checker accepted it. Document that
limitation; do not add trailer parsing or special formatting to this helper.

Assemble subject and formatted optional body with one separating blank line,
then reuse the checker's public validation path. Keep the checker, width policy
and Git `stripspace` comment/scissors behavior unchanged, including Magit
verbose-message semantics. Existing hooks never format bodies through this
helper; it only adapts explicit Make input. Retain normal Git message cleanup
rather than introducing another comment/scissors parser.

## Literal transport and commit scope

The current Make `_SHELL_VALUE` quotes apostrophes for the shell, but recursive
Make interpolation/export can evaluate input first. Capture raw SUBJECT/BODY
without recursive expansion, avoid inline shell interpolation, and use a Python
argument list for external commands. Apostrophes, quotes, backticks, dollar
signs, Make-looking expressions and multiline BODY must reach the adapter as
literal data. Formatting may reflow prose but must never execute its content.
Caller shell quoting remains necessary; document one safe usage form. Do not
use shell evaluation, Make `eval` or recursive input expansion.

Commit the caller's existing index in its worktree. No auto-staging, amendment,
empty-commit option, publication, hook/configuration changes or bypasses are in
scope. Preserve ordinary Git/hook diagnostics and failure; hook refusal must
not advance HEAD. Normal hook side effects are not rolled back. Add only the
small adapter, Make help and minimal
[CONTRIBUTING usage](../../../CONTRIBUTING.md#commits-and-pull-requests), with
precise types under [engineering conventions](../../engineering.md). This is
one leaf targeting about five-minute review including focused tests.

- **AC-1 TODO** Given prose, bullets, long tokens and marked commands, the
  adapter formats only BODY through isolated native rumdl, leaves SUBJECT
  untouched, and uses the unchanged checker to accept the formatted message or
  reject unchanged incompatible literal text. Missing BODY yields subject-only
  text; the trailer limitation is stated without dedicated preservation.

  Validation: criterion-marked adapter integration tests use real rumdl and the
  existing public checker for representative paragraph/bullet/token input,
  marked 72/73-column commands and formatter failure. Inspect formatting scope,
  configured width reuse and unchanged checker/comment/scissors behavior;
  reuse its existing regressions without an exhaustive MD013 or Markdown suite.
- **AC-2 TODO** Given quoting and Make/shell-looking input, the Make route
  transports literal data safely and commits only staged changes with ordinary
  hooks, or fails visibly with HEAD unchanged.

  Validation: focused Make routing tests cover quotes, backticks, dollars,
  multiline BODY and `$(shell ...)`/`${...}` text, asserting exact adapter input
  and no execution sentinel effects. Reuse
  [Make helpers](../../../test/make/support.py) and
  [disposable Git/process helpers](../../../test/script/commit_message_support.py)
  for real successful commits, unstaged-file preservation and hook refusal,
  including Conventional Commit rejection. Shims prove routing only; inspect
  stored messages/refs for commit outcomes. Bound subprocess tests, run affected
  lint/type/doc/ac checks and review minimal usage/literal/trailer guidance
  under [testing](../../testing.md) and
  [integration guidance](../../testing-integration.md).
