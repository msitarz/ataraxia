# Real source CSV context resources

After source forwarding delivery, own new
`test/ataraxia/integration/test_source_csv.py`, its typed local CSV arrangements
and strict include. This crosses the real source/provider boundary. Use actual
BarProvider and SourceNode, not tracking doubles; require their already adopted
module contracts without importing test fixtures.

Separate exhaustion, context-body exception, and early-context-exit cases.
Exhaustion sends complete independently expected Bars through the public factory
runner. Early exit reads/sends one Bar while another remains, then leaves the
source's `with` scope. The body exception preserves the exact error object at
the caller after entering/opening and reading valid input. For each case capture
the actual file handle after context entry, verify the relevant literal values,
and assert that handle closed after the scope exits. Do not confuse the provider
iterator with a closable compute generator or infer closure from callback
counts.

- **AC-1 DONE** Given real CSV/source contexts, exhaustion, a propagated body
  error and early scope exit each preserve literal source values and close the
  genuine provider resource at the source-owned context boundary.

  Validation: review distinct lifecycle paths and captured handle state; run all
  four input modules, complete product suite and the input group's checks.
  Compute-generator exhaustion/error/explicit close remain unverified here and
  belong to the future Compute delivery, not this criterion.
