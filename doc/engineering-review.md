# Engineering judgment in review

Read this when changing or reviewing code or tests. Apply these questions as
you make small changes and when you review the completed result:

- Does the change implement the Work's smallest coherent design?
- Can repeated state or interpretation be derived once?
- Do new types with the same meaning belong together?
- For distinct variants with shared fields or behavior, would a shared base or
  helper clarify their common contract, including for diagnostics?
- Do checks and abstractions earn their complexity?
- Do types, behavior, tests, and effects live with the responsibility that
  owns them?

Keep intentional overlap when it is clearer and explain it in the PR. Move code
or extract a helper only when that clarifies its responsibility and resulting
contract. Review may accept the design unchanged; no refactor or comment quota
applies.

Use [engineering conventions](engineering.md) for the lasting rules on
boundaries, modeling, pure decisions, ports, effects, readable conditions, and
type precision. [Testing](testing.md) owns test policy and observation
boundaries; [test ownership](test-ownership.md) owns cleanup decisions.
