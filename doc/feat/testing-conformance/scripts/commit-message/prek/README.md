# Prepared-project prek filename forwarding

After configured Git delivery, own new
`test/script/integration/test_commit_message_prek.py`, narrowly scoped
`test/script/commit_message_prek.py` arrangement helper, and their strict
includes. Move only `test_prek_passes_message_filename`, splitting its loop into
named success and refusal tests; remove the then-empty legacy module. Reuse
`test/script/commit_message_support.py` without adding fixtures to earlier
leaves or conftest.

Use the prepared project's actual `.venv` prek and real configured
`commit-message-format` hook/checker in a disposable minimal project. Preserve
the repository hook definition and real uv entry; do not substitute a fake
prek/checker or silently maintain a second hook policy. Supply explicit HOME,
TMPDIR, isolated Git config and disposable caches; arrange already prepared
tools for offline/no-sync execution without network installs, checkout writes,
global prek, or a hard-coded Homebrew path. Missing preparation is a reported
setup gap, not a reason to repair tool-location or launcher policy in this leaf.

Retain `fix: change` success and `fix: change\nNo gap` refusal through actual
`--hook-stage commit-msg --commit-msg-filename` forwarding. Assert exact 0/1
exit, distinctive configured-hook status and refusal reason, and complete
unchanged message bytes. Compare contractual output literally; avoid locking
incidental progress formatting. Preserve other disposable project input files
and Git refs. Precisely annotate every new helper/fixture/test and keep the
success/refusal tests separate with Given/When/Then and slice docstrings.

- **AC-1 DONE** Given the prepared offline project arrangement, real prek
  forwards each named message file to our configured checker, returns exact
  success/refusal effects, and preserves message/project inputs and Git refs
  without relying on global installation or changing caller state.

  Validation: inspect preparation dependencies, copied configuration, literal
  effects and strict includes; run both cases and all delivered commit-message
  modules, complete script suite, strict typing, lint/format, doc/ac checks, and
  latest-head full CI before merge. Report missing tools, unexpected skips,
  installation attempts, or launcher incompatibility as unverified blockers.
