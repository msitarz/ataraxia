# Wire scoped rumdl fence tools into doc-check

Invoke the repository's
[stdin validator](../../../../../script/validate_mermaid.py). Configure a
Mermaid lint tool in `pyproject.toml` under
`[tool.rumdl.code-block-tools]`,
its `tools` and `languages.mermaid` sections with `enabled=true`. Invoke the
prepared Python validator with stdin enabled, `stdout=false`,
`on-error="fail"`, `on-missing-tool-binary="fail"` and a
30,000-millisecond timeout so a missing validator cannot silently skip the
check. Keep other languages unconfigured with their native ignored default.

Add a small scoped target, such as `doc-check-mermaid`, using rumdl
`check --only-code-block-tools --no-cache` with selected `ARGS` paths or `.`
by default. Use existing config exclusions, `force-exclude` and gitignore
policy; directory scans omit ignored files, explicitly named gitignored files
are processed, and configured excludes still apply. The probe's cached success
following a validator-only edit justifies `--no-cache`; no cache framework or
cache-invalidation investigation is needed.

Compose that target sequentially after existing `doc-check` stages. Disable
code-block tools in the existing selected-path-plus-`.` link-graph stage and
selected formatting stage so neither validates Mermaid at graph scope or
repeats it. Preserve their current ordering and fail-fast behavior. The scoped
stage follows rumdl's native error policy: reached validator/tool failures fail
the target; do not add custom aggregation, categories or continued execution.
Keep `doc-format` a formatting-only operation. All checking remains read-only
and offline/no-sync. `verify-check` and existing Check CI reach it through
`doc-check ARGS=`; no new CI job or setup route is needed.

Reuse the existing real-tool
[Markdown sandbox/tests](../../../../../test/make/integration/test_markdown_tools.py)
with only necessary validator-file copying and focused assertions. Keep
existing formatting/link/missing-tool regressions at their current owners.
Document the native blockquote limitation and command help as needed; do not
promise full container support or GitHub/browser parity.

- **AC-1 TODO** Given selected files/directories and an invalid Mermaid fence
  outside them, `doc-check` validates only selected Mermaid while preserving
  the full existing link graph and selected formatting checks. The ordinary
  stages have fence tooling disabled and the scoped stage reaches the actual
  validator with native failure diagnostics and the configured deadline;
  missing validator binaries fail rather than silently skip.

  Validation: criterion-marked Make integration tests reuse the real Markdown
  sandbox, rumdl and validator for selected valid/invalid fences, an unselected
  invalid fence and the existing broken-link regression. Inspect command/config
  routing for disabled ordinary stages, missing-binary failure and the 30,000ms
  tool timeout; bounded test calls prove actual validator execution, not only
  shim routing. Preserve
  native fail-fast behavior without an exhaustive parser/timeout matrix.
- **AC-2 TODO** Given empty `ARGS`, valid or malformed repository Mermaid and
  no-diagram selections, the scoped uncached stage uses default `.` and current
  exclusion policy, succeeds or fails through native rumdl behavior, and emits
  no SVG or checkout changes offline. Ordinary-stage failures still stop
  `doc-check` before the scoped stage.

  Validation: focused real-tool Make tests cover default selection, relevant
  exclusion behavior, valid/invalid and no-diagram cases with bounded subprocess
  calls and file observations. Inspect `--no-cache`, offline/no-sync settings,
  unchanged CI routing and formatting-only `doc-format`; run default
  `make doc-check` on the delivery revision plus affected lint/type/doc/ac
  checks. Independently review help and the stated blockquote limitation under
  current [testing](../../../../testing.md),
  [test ownership](../../../../test-ownership.md) and
  [evidence policy](../../../../validation.md).
