# SPDX-License-Identifier: Apache-2.0
"""Load and narrowly adapt the reviewed crossover sample expectation."""

import json
from pathlib import Path


def load_sample_expected() -> object:
    """Load the static golden as an opaque whole-value expectation."""
    path = Path(__file__).parent / "fixtures" / "cli" / "crossover_expected.json"
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_sample_paths_and_order(value: object, project: Path) -> object:
    """Normalize actual output's checkout-specific paths and shard order.

    The CLI emits absolute strategy and shard paths, and shard order follows
    unspecified directory iteration. Convert paths to project-relative form and
    sort by shard path; golden paths are already stable. Preserve every other
    field, including unexpected ones, for complete comparison.
    """
    if not isinstance(value, list):
        raise ValueError("sample CLI result must be a JSON array")

    project_root = project.resolve()
    normalized: list[tuple[str, dict[str, object]]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("sample CLI result entries must be JSON objects")
        fields: dict[str, object] = {}
        for key, field_value in item.items():
            if not isinstance(key, str):
                raise ValueError("sample CLI result keys must be strings")
            fields[key] = field_value

        shard_path = fields.get("shard_path")
        strategy_path = fields.get("strategy_path")
        if not isinstance(shard_path, str) or not isinstance(strategy_path, str):
            raise ValueError("sample CLI results must include both path fields")
        relative_shard = _relative_project_path(shard_path, project_root)
        fields["shard_path"] = relative_shard
        fields["strategy_path"] = _relative_project_path(strategy_path, project_root)
        normalized.append((relative_shard, fields))

    return [fields for _, fields in sorted(normalized, key=lambda item: item[0])]


def _relative_project_path(value: str, project_root: Path) -> str:
    path = Path(value)
    if not path.is_absolute():
        raise ValueError("sample CLI paths must be absolute")
    return path.resolve().relative_to(project_root).as_posix()
