# Configured comments and real Git-hook effects

After checker delivery, own new
`test/script/integration/test_commit_message_git.py` and its strict include.
Move only `test_verbose_diff_below_scissors` and
`test_git_commit_hook_and_configured_comments` from the legacy module. Use
`test/script/commit_message_support.py` and
`test/script/fixtures/commit_message_hook.py`; change support only for a
necessary bounded interface correction, reporting any larger scope before
expansion.

Retain all six combinations: comment prefixes `#`, `;`, `//` with short accepted
or over-width refused bodies. Configure real Git `core.commentString`; assert
0/1 exits, independent complete checker outcomes, ignored long diff content,
and unchanged message bytes. Parameter IDs identify both prefix and outcome.

Retain the real `commit-msg` lifecycle using `core.commentChar=;`: the missing
separator commit refuses with its exact Git exit and distinctive checker reason,
leaving complete refs and unborn HEAD unchanged. The accepted empty commit
strips configured comments and stores independently expected complete message
text, including newline behavior. Capture refs before/after refusal rather than
using only failed `rev-parse`; all Git/checker processes use isolated explicit
state and timeouts. Do not repair Git or generated project hook launchers.

- **AC-1 DONE** Given configured disposable Git repositories, scissors preserve
  checker outcomes and input bytes, while the installed real hook refuses
  without ref changes and accepts exactly the expected stored commit content.

  Validation: review all six scissors cases and the lifecycle's literal outputs,
  exact failure effects, hook source and isolation; run focused migrated cases,
  all delivered commit-message modules and legacy remainder, strict typing,
  lint/format, doc/ac checks, and latest-head full CI before merge.
