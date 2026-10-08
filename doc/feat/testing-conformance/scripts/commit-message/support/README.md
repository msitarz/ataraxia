# Typed commit-message arrangements

Own new `test/script/commit_message_support.py` and named executable fixture
`test/script/fixtures/commit_message_hook.py`, plus their precise strict-Pyrefly
includes. Reuse existing process patterns without importing registry or Make
domain arrangements. Leave legacy tests, shared conftest, and production code
unchanged; consumers adopt this support only after it merges.

Provide narrowly typed captured results (exit, stdout, stderr, combined
diagnostics), timeout-owning execution, disposable message/repository setup, Git
invocation and complete refs/HEAD observations. Supply explicit HOME and TMPDIR
under `tmp_path`, controlled PATH, disabled system/global Git config, local
identity/signing/hook configuration, and no inherited caller Git overrides. The
real checker and Git remain external processes. Hook source lives in the named
typed executable fixture, with explicit interpreter/checker inputs; do not
generate substantial source strings or change installed hook launchers.

This leaf owns no prek project arrangement: that helper is defined with its
consumer in the prek leaf. Keep support small; return a split if precise typing,
fixture construction, or environment setup exceeds the review target.

- **AC-1 TODO** Given the support artifact, later checker and Git consumers can
  use precise typed arrangements with captured bounded processes and disposable
  state, without forward fixture dependencies or caller configuration leakage.

  Validation: manually inspect signatures, fixture source, isolation and Git
  observations; run strict typing on both new files, lint/format, doc/ac checks,
  and the unchanged legacy module for compatibility. Runtime adoption is
  verified by the following consumer leaves; do not claim it from typing alone.
