# Isolated real-command support

After argument units, own `cli_process.py` and its strict include. Provide
precisely typed captured exit/stdout/stderr results, timeout-owning execution,
disposable output/arrangement state and explicit child cwd/environment. Invoke
the shipped `uv run --no-sync ataraxia` using prepared project tools; preserve
the PATH needed to locate tools and explicitly isolate HOME/TMPDIR and caches.
Use prepared offline tools, not network installs or global environment
accidents.

Sample flows read the shipped example/shards; other files are created under
tmp_path. Support disposable cwd for default-output flows while explicitly
selecting the prepared project. Keep checkout inputs unchanged and output
disposable. Acceptance
support imports no package internals and replaces no product components. No
new fake executable, launcher/tool-location policy or shared helper migration.
Consumers follow after this owner merges; no forward fixture dependencies.

- **AC-1 DONE** Given prepared tools and disposable arrangements, typed command
  support executes the real shipped entry point with bounded captured processes
  and explicit state without caller/checkout mutation or product doubles.

  Validation: inspect command/environment/cwd/timeout signatures and state
  isolation; run strict/lint/doc/ac checks and legacy compatibility cases.
  Actual command behavior is verified by following acceptance leaves.
