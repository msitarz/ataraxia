# Worktree creation helper

Provide precise typed disposable Git/process support with explicit isolated Git
configuration, timeouts, captured stdout/stderr, and observable refs/worktree
registrations. Use a real fixture-file uv setup fake that logs arguments and
relevant environment, creates destination environments from usable cache, and
simulates cache/setup verification failures. Reuse delivered Make support
narrowly; no generic fixture framework or production change. Include all new
helper/fixture/smoke-test files in normal strict Pyrefly.

- **AC-1 TODO** Given a disposable committed repository and usable cache, real
  Make/Git create a branch worktree; fixture setup creates its local environment
  and records destination-local cache/project paths and offline flags.

  Validation: run a small criterion-marked real-Make creation smoke test and
  strict typecheck; independently inspect isolated configuration, timeout-owning
  helpers, captured observations, and latest-head full CI.
