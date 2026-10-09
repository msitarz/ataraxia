# Hypothesis pilots

Introduce Hypothesis after the relevant boundary cleanup, preserving named
examples and independently specified expectations.

## Delivery map

- **DONE** Adoption: locked development dependency, bounded local/CI settings
  and narrow lasting guidance.
- **TODO** [Window](window/README.md): newest-first truncation at every prefix
  against an independent sequence model.
- **TODO** [Work paths](workpaths/README.md): canonical existing contracts and
  normalized/escaping-path rejection, including symlink containment.
- **TODO** [Make arguments](makearguments/README.md): literal four-value
  transport through real Make with absent execution markers.

```mermaid
flowchart LR
    C[Delivered boundary and golden cleanup] --> A[Adoption]
    A --> W[Window pilot]
    A --> P[Work-path pilot]
    A --> M[Make-argument pilot]
```

Adoption adds the development dependency and lockfile plus narrowly scoped
owned guidance/configuration. Start with 100 examples for in-process properties
and 25 for subprocess properties. Disable subprocess timing deadlines while
retaining process timeouts; use deterministic CI generation. Construct fresh
mutable/filesystem state per example instead of suppressing fixture health
checks. Keep generated inputs bounded and retain named hostile examples.

Each pilot depends on adoption and its corresponding cleanup. These pilots do
not authorize a wholesale conversion or new broker/Git state machines.
Merge these contracts before implementation. Deliver adoption first, then
window, Work paths and Make arguments, serializing shared settings/maps. Each
complete leaf includes helpers/type changes within about five-minute review;
escalate and merge revised contracts before expansion. Reuse full-folder strict
coverage for `src`, `script`, `test` and `example`, with the existing
intentional-negative expectations route, rather than per-file lists. No
production repair or performance claim. Preserve named cases and provenance.

- **AC-1 TODO** Given the adopted bounded settings and fresh per-example state,
  the three independently reviewed pilots prove ordering/truncation, canonical
  Work containment and literal Make transport without replacing named examples
  or weakening behavior, type precision or isolation.

  Validation: independently review all four child outcomes, selected generated
  and named-case execution, settings/isolation and strict-folder evidence, then
  run doc/ac checks. Final-head full CI remains the separate merge gate.
