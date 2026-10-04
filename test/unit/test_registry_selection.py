# SPDX-License-Identifier: Apache-2.0
"""Exercise approved preparation selection and retained failure boundaries."""

import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "script" / "registry_selection.py"
SPEC = importlib.util.spec_from_file_location("registry_selection", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
selection = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = selection
SPEC.loader.exec_module(selection)


def preparation(tmp_path):
    """Create dedicated resolver caches and externally provisioned record."""
    cache, repository = tmp_path / "cache", tmp_path / "repository"
    repository.mkdir()
    declarations = {}
    for name in selection.DECLARATIONS:
        (repository / name).write_text("frozen declaration")
        declarations[name] = selection.digest(repository / name)
    evidence = tmp_path / "successful-setup.log"
    evidence.write_text("actual Make setup/hook evidence reviewed independently")
    files, links, packages = {}, {}, []
    for root in sorted(selection.ROOTS):
        archive = f"{root}/archive-v0/dependency"
        wheel = f"{root}/wheels-v6/pypi/dependency/1.0-py3-none-any"
        contents = {
            f"{archive}/dependency.py": "pinned dependency",
            f"{archive}/dependency-1.0.dist-info/METADATA": (
                "Name: dependency\nVersion: 1.0\n"
            ),
            f"{wheel}.http": "opaque HTTP metadata",
        }
        if root == "prek/cache/uv":
            contents[f"{root}/simple-v25/pypi/dependency.rkyv"] = "opaque metadata"
        for name, content in contents.items():
            path = cache / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            files[name] = selection.digest(path)
        target = "../../../archive-v0/dependency"
        (cache / wheel).symlink_to(target)
        links[wheel] = target
        packages.append({
            "root": root,
            "name": "dependency",
            "version": "1.0",
            "wheel": wheel,
            "archive": archive,
            "origin": selection.CONDITION["index"],
            "basis": "reviewed dependency preparation",
            "trace": f"{archive}/dependency-1.0.dist-info/METADATA",
        })
    data = {
        "condition": selection.CONDITION,
        "declarations": declarations,
        "evidence": {evidence.name: selection.digest(evidence)},
        "derivation": "each package mapped to reviewed preparation evidence",
        "files": files,
        "links": links,
        "packages": packages,
    }
    record = tmp_path / "record.json"
    record.write_text(json.dumps(data))
    return cache, repository, record, data


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
def test_selection_preserves_both_resolvers_and_ignores_contamination(tmp_path):
    """AC-1: only declared payloads/metadata enter selection; raw cache is unchanged."""
    cache, repository, record, data = preparation(tmp_path)
    for name in (
        "uv/sdists-v9/editable/project.whl",
        "uv/interpreter-v4/env",
        "answers",
    ):
        path = cache / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("unselected project data")
    before = {p: p.read_bytes() for p in cache.rglob("*") if p.is_file()}
    result = selection.select(cache, record, selection.digest(record), repository)
    assert result.files == data["files"]
    assert result.links == data["links"]
    assert {p: p.read_bytes() for p in before} == before
    assert len(result.packages) == 2


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.parametrize(
    "damage", ["file", "link", "declaration", "evidence", "record"]
)
def test_changed_preparation_or_cache_is_rejected(tmp_path, damage):
    """AC-1/AC-2: changed entries, external links and stale inputs fail closed."""
    cache, repository, record, data = preparation(tmp_path)
    expected = selection.digest(record)
    if damage == "file":
        (cache / next(iter(data["files"]))).unlink()
    elif damage == "link":
        link = cache / next(iter(data["links"]))
        link.unlink()
        link.symlink_to(repository)
    elif damage == "declaration":
        (repository / "uv.lock").write_text("changed")
    elif damage == "evidence":
        (tmp_path / "successful-setup.log").write_text("changed")
    else:
        record.write_text("{}")
    with pytest.raises(ValueError):
        selection.select(cache, record, expected, repository)


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.parametrize(
    "damage", ["uv", "index", "platform", "layout", "metadata", "undeclared", "version"]
)
def test_unsupported_approved_record_fails(tmp_path, damage):
    """AC-2: unsupported conditions, absent metadata and declarations fail."""
    cache, repository, record, data = preparation(tmp_path)
    if damage in selection.CONDITION:
        data["condition"] = dict(selection.CONDITION)
        data["condition"][damage] = "unsupported"
    elif damage == "metadata":
        del data["files"][next(p for p in data["files"] if p.endswith(".rkyv"))]
    elif damage == "undeclared":
        data["files"]["answers"] = "untrusted"
    else:
        data["packages"][0]["version"] = "2.0"
    record.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        selection.select(cache, record, selection.digest(record), repository)


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
def test_cli_retains_failure_and_never_overwrites_destination(tmp_path):
    """AC-2: failed selection retains diagnostics; existing destination is untouched."""
    destination = tmp_path / "result"
    argv = [
        str(SCRIPT),
        "--cache",
        str(tmp_path / "cache"),
        "--record",
        str(tmp_path / "absent"),
        "--expected",
        "0" * 64,
        "--destination",
        str(destination),
    ]
    with patch.object(sys, "argv", argv):
        assert selection.main() == 1
    original = (destination / "failure.txt").read_bytes()
    with patch.object(sys, "argv", argv):
        assert selection.main() == 1
    assert (destination / "failure.txt").read_bytes() == original


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
def test_cli_success_and_input_cache_destination_guard(tmp_path):
    """AC-1/AC-2: serialize provenance; reject destinations within source cache."""
    cache, repository, record, data = preparation(tmp_path)
    destination = tmp_path / "result"
    argv = [
        str(SCRIPT),
        "--cache",
        str(cache),
        "--record",
        str(record),
        "--expected",
        selection.digest(record),
        "--destination",
        str(destination),
    ]
    with (
        patch.object(sys, "argv", argv),
        patch.object(Path, "cwd", return_value=repository),
    ):
        assert selection.main() == 0
    result = json.loads((destination / "selection.json").read_text())
    assert result["files"] == data["files"]
    assert result["packages"] == data["packages"]
    argv[-1] = str(cache / "forbidden")
    with patch.object(sys, "argv", argv):
        assert selection.main() == 1
    assert not (cache / "forbidden").exists()


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
def test_record_is_parsed_from_the_single_accepted_read(tmp_path):
    """AC-1: a changing record cannot substitute unapproved bytes after hashing."""
    cache, repository, record, data = preparation(tmp_path)
    expected = selection.digest(record)
    original_read = Path.read_bytes
    reads = []

    def changing_read(path):
        content = original_read(path)
        if path == record:
            reads.append(path)
            record.write_text("{}")
        return content

    with patch.object(Path, "read_bytes", autospec=True, side_effect=changing_read):
        result = selection.select(cache, record, expected, repository)
    assert result.files == data["files"]
    assert reads == [record]
    assert record.read_text() == "{}"
