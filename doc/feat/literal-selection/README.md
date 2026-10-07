# Literal selection investigation

Investigate whether tooling or guidance should identify suitable closed string
domains. The first seed is `arrange_changed_input` in
[registry selection inputs](../../../test/script/selection_inputs.py),
before local Literal adoption:

```python
def arrange_changed_input(case: PreparedSelection, change: str) -> None:
    changed = ROOT / "test/script/fixtures/registry_selection/changed.txt"
    destinations = {
        "declaration": case.repository / "uv.lock",
        "evidence": case.directory / "successful-setup.log",
    }
    match change:
        case "declaration" | "evidence":
            shutil.copyfile(changed, destinations[change])
        case "file":
            (case.cache / "uv/archive-v0/dependency/payload.txt").unlink()
        case "link":
            link = case.cache / "uv/wheels-v6/pypi/dependency/1.0-py3-none-any"
            link.unlink()
            link.symlink_to(case.repository)
        case "record":
            shutil.copyfile(
                ROOT / "test/script/fixtures/registry_selection/unapproved.json",
                case.record,
            )
        case _:
            raise ValueError(f"unknown fixture input: {change}")
```

A second historical seed is the original record-input signature:

```python
def copy_selection_fixture(directory: Path, record_name: str) -> PreparedSelection: ...
```

Its supported names are accepted, uv, index, platform, layout, metadata,
undeclared and version, a distinct domain from the five changed-input names.
Paths and digest strings do not define finite domains.

Both local examples now use distinct Literal aliases, with domain-specific
narrowing after `parameter_name` validates the untyped `request.param` as `str`.
The changed-input match retains its unknown-name ValueError. This maintainer
adoption supplies concrete examples, not tooling findings or repository-wide
policy. Compare Literal with retaining `str`, and explain when Enum adds useful
identity or behavior. Preserve truthful boundary/caller types without casts or
checker suppression, runtime rejection and one authoritative domain inventory.

Compare the locked Ruff/Pyrefly capabilities with other tooling and guidance
only. Match arms alone cannot establish a closed domain: assess open-domain
matches, meaningful defaults, overlapping conditions and future extensions.
Review false positives and safe adoption limits with positive and negative
examples. This Work recommends a direction; no general rule adoption or tooling
investigation result is delivered by this contract.

- **AC-1 TODO** An inspectable recommendation compares Literal, retained str
  and justified Enum usage, evaluates tooling versus guidance for suitable
  closed string domains, and explains truthful boundary/caller typing, runtime
  rejection, false positives and inventory ownership with examples; it states
  whether a separate adoption Work is warranted.

  Validation: independently review pinned/locked tool-version and capability
  evidence, candidate tradeoffs and the preserved seed/caller boundary. Run
  positive/negative typing and runtime examples through Make and retain their
  outcomes; check open-domain/default/overlap/extension counterexamples against
  engineering/testing guidance. Keep the complete investigation reviewable in
  five minutes; split before expansion.
