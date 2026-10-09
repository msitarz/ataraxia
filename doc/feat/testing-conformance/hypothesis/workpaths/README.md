# Generate canonical Work paths and containment failures

After adoption, own new `test/script/unit/test_work_paths.py` for the public
`resolve_work_file(root: Path, work: str) -> Path`. Preserve existing named
acceptance-command/path-refusal tests unchanged. Generate 1 through 3 directory
segments of 1 through 8 ASCII letters/digits/underscore/hyphen, ending in either
`README.md` or `spec.md`. Within a fresh temporary context per example, create
the canonical file and expect its independently arranged resolved identity.

Generate rejection cases by named construction, not by copying the validator's
regex or normalization algorithm: empty input, absolute path, parent traversal,
dot/repeated-separator noncanonical spelling, invalid character, wrong suffix
and absent file. Assert `ValueError` and the corresponding contextual reason,
including the requested path for absent/escaping resolved files. Explicit
examples retain each category. Create fresh inside-root and outside-root files
with relative symlinks: an existing inside target is accepted, an outside target
is rejected, without mutating the checkout. Own these bounded arrangements in
the new test module; unsupported platform symlinks must be reported as
unverified, not silently dropped. No production helper/interface changes.

Use 100 in-process examples, no function-scoped mutable fixture or health-check
suppression. Precisely type all strategies/arrangements on the existing strict
folder route; retain independent path intent and observed failure provenance.

- **AC-1 TODO** Given freshly arranged canonical contracts and named malformed
  or escaping variants, the real resolver accepts exactly the intended existing
  contained identities and rejects invalid/noncanonical/absent/outside paths
  with contextual failures, including symlinks, without shared example state.

  Validation: review construction/oracles and all category/symlink examples;
  run generated cases plus existing named acceptance-command cases through Make,
  inspect strict-folder typing and isolation, then run doc/ac checks.
