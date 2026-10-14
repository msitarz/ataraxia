# Literal selection investigation

Investigate whether tooling or guidance should identify suitable closed string
domains. The first seed is `arrange_changed_input` in
[the predecessor before Literal adoption](https://github.com/msitarz/ataraxia/blob/403081936833e579384d138aa0da43517ba6d09c/test/script/selection_inputs.py#L93).
The later
[reviewed source revision](https://github.com/msitarz/ataraxia/blob/5d37d04b0640e1a72c0751ddb7a9141783583ceb/test/script/selection_inputs.py#L93)
already includes the local Literal adoption from
[the narrowing change](https://github.com/msitarz/ataraxia/commit/63d2a7b).
The frozen predecessor source preserves the condition and fixture context after
the selector cleanup:

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

[`copy_selection_fixture` before narrowing](https://github.com/msitarz/ataraxia/blob/403081936833e579384d138aa0da43517ba6d09c/test/script/selection_inputs.py#L28):

```python
def copy_selection_fixture(directory: Path, record_name: str) -> PreparedSelection: ...
```

Its supported names are accepted, uv, index, platform, layout, metadata,
undeclared and version, a distinct domain from the five changed-input names.
Paths and digest strings do not define finite domains.

The preserved adopted revision uses distinct Literal aliases, with
domain-specific narrowing after `parameter_name` validates the untyped
`request.param` as `str`; the changed-input validator retains unknown-name
`ValueError` rejection. These are historical examples, not live helpers in the
current checkout. The linked investigation report records the bounded tool
comparison and recommendation. Preserve truthful boundary/caller types without
casts or checker suppression, runtime rejection and one authoritative domain
inventory.

See the bounded [investigation report](investigation.md) for historical
provenance, pinned-tool probes, candidate comparison, and recommendation.

Compare the locked Ruff/Pyrefly capabilities with other tooling and guidance
only. Match arms alone cannot establish a closed domain: assess open-domain
matches, meaningful defaults, overlapping conditions and future extensions.
Review false positives and safe adoption limits with positive and negative
examples. This Work investigates a direction; it does not adopt general policy
or a tooling rule.

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
