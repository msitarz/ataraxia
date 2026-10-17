# Engineering judgment in review

Read this when changing or reviewing code or tests. Ask whether the change
implements the Work's smallest coherent design. Apply these questions as you
make small changes and when you review the completed result:

- Can repeated state or interpretation be derived once?
- Do new types with the same meaning belong together? For distinct variants
  with shared fields or behavior, would a shared base or helper clarify their
  common contract, including for diagnostics?
- Do checks and abstractions earn their complexity, and do types, behavior,
  tests, and effects live with the responsibility that owns them?
- Would intentional overlap be clearer than shared structure? If so, explain
  it in the PR. Move code or extract a helper only when that makes its
  responsibility and resulting contract clearer.

Use [engineering conventions](engineering.md) for the lasting rules on
boundaries, modeling, pure decisions, ports, effects, readable conditions, and
type precision. [Testing](testing.md) owns test policy and observation
boundaries; [test ownership](test-ownership.md) owns cleanup decisions.
