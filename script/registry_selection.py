# SPDX-License-Identifier: Apache-2.0
"""Validate registry selections rooted in independently reviewed preparation."""

import argparse
from dataclasses import asdict, dataclass
from email.parser import Parser
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import cast

ROOTS = {"uv", "prek/cache/uv"}
CONDITION = {
    "uv": "0.12.19",
    "prek": "0.5.3",
    "python": "3.14",
    "platform": "macos-x86_64",
    "index": "https://pypi.org/simple",
    "config": "UV_NO_CONFIG=true",
    "layout": "archive-v0/wheels-v6/simple-v25",
}
DECLARATIONS = {"uv.lock", "pyproject.toml", ".pre-commit-config.yaml"}


def digest(path: Path) -> str:
    """Return a file's SHA256."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapping(value: object) -> dict[str, object]:
    """Narrow an external JSON object after checking its keys.

    Returns:
        The checked object.

    Raises:
        ValueError: If keys are not strings.
    """
    if not isinstance(value, dict) or not all(isinstance(k, str) for k in value):
        raise ValueError("expected a JSON object with string keys")
    return cast(dict[str, object], value)


def strings(value: object) -> dict[str, str]:
    """Validate a string-valued inventory.

    Returns:
        The checked inventory.

    Raises:
        ValueError: If values are not strings.
    """
    result = mapping(value)
    if not all(isinstance(v, str) for v in result.values()):
        raise ValueError("expected string inventory values")
    return cast(dict[str, str], result)


def relative(value: str) -> Path:
    """Reject noncanonical and escaping inventory paths.

    Returns:
        The checked relative path.

    Raises:
        ValueError: If the path is unsafe.
    """
    path = Path(value)
    if path.is_absolute() or path.as_posix() != value or ".." in path.parts:
        raise ValueError(f"unsafe inventory path: {value}")
    if not path.parts or value == ".":
        raise ValueError("empty inventory path")
    return path


def regular(root: Path, name: str) -> Path:
    """Require a regular entry with no symlink ancestors.

    Returns:
        The regular file path.

    Raises:
        ValueError: If missing or linked.
    """
    path = root / relative(name)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError(f"linked file or ancestor: {name}")
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"missing or external file: {name}")
    return path


@dataclass(frozen=True)
class Package:
    """Declared registry artifact and its reviewed preparation derivation."""

    root: str
    name: str
    version: str
    origin: str
    wheel: str
    archive: str
    basis: str
    trace: str


@dataclass(frozen=True)
class Selection:
    """Compose-ready selected entries and their preparation trust anchor."""

    files: dict[str, str]
    links: dict[str, str]
    packages: tuple[Package, ...]
    preparation_sha256: str


def packages(value: object) -> tuple[Package, ...]:
    """Validate package declarations at the JSON boundary.

    Returns:
        Declared package records.

    Raises:
        ValueError: If declarations are absent.
    """
    if not isinstance(value, list) or not value:
        raise ValueError("preparation must declare packages")
    result = []
    for item in value:
        record = strings(item)
        if record.keys() != Package.__dataclass_fields__.keys():
            raise ValueError("incomplete package provenance record")
        result.append(
            Package(
                record["root"],
                record["name"],
                record["version"],
                record["origin"],
                record["wheel"],
                record["archive"],
                record["basis"],
                record["trace"],
            )
        )
    return tuple(result)


def package_entries(
    cache: Path, package: Package, files: dict[str, str], links: dict[str, str]
) -> set[str]:
    """Check a declared wheel's payload and opaque resolver records.

    Returns:
        The allowed file entries for this wheel.

    Raises:
        ValueError: If entries contradict the declaration or supported layout.
    """
    root, name, version = package.root, package.name, package.version
    if root not in ROOTS or package.origin != CONDITION["index"]:
        raise ValueError("unsupported registry root or origin")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError("noncanonical package name")
    wheel, archive = package.wheel, package.archive
    if not wheel.startswith(f"{root}/wheels-v6/pypi/{name}/{version}-"):
        raise ValueError("wheel does not match declared package")
    if relative(archive).parent != Path(root) / "archive-v0":
        raise ValueError("unsupported archive layout")
    if links.get(wheel) != str(Path("../../..") / "archive-v0" / Path(archive).name):
        raise ValueError("wheel/archive link mismatch")
    payload = {p for p in files if p.startswith(archive + "/")}
    metadata = {f"{wheel}.http"}
    if root == "prek/cache/uv":
        metadata.add(f"{root}/simple-v25/pypi/{name}.rkyv")
    if not payload or not metadata <= files.keys():
        raise ValueError("missing payload or complete resolver metadata")
    metadata_files = [
        p
        for p in payload
        if p.endswith(".dist-info/METADATA")
        and len(Path(p).relative_to(archive).parts) == 2
    ]
    if len(metadata_files) != 1:
        raise ValueError("expected one wheel METADATA")
    if package.trace != metadata_files[0] or not package.basis:
        raise ValueError("missing package preparation derivation")
    info = Parser().parsestr(regular(cache, metadata_files[0]).read_text())
    normalized = re.sub(r"[-_.]+", "-", info.get("Name", "")).lower()
    if normalized != name or info.get("Version") != version:
        raise ValueError("payload METADATA contradicts preparation")
    if any(p.endswith(("/direct_url.json", "/pyvenv.cfg")) for p in payload):
        raise ValueError("local-source or environment payload")
    return payload | metadata


def select(cache: Path, record: Path, expected: str, repository: Path) -> Selection:
    """Validate an externally accepted preparation record without modifying cache.

    The caller must obtain expected from independent review, not from the record.
    Hash validation preserves that provenance; it does not authenticate downloads.

    Returns:
        Selected entries with provenance bound to the preparation digest.

    Raises:
        ValueError: If preparation or cache entries contradict the supported input.
    """
    record_bytes = record.read_bytes()
    if (
        not re.fullmatch(r"[0-9a-f]{64}", expected)
        or hashlib.sha256(record_bytes).hexdigest() != expected
    ):
        raise ValueError("preparation digest differs from external acceptance")
    data = mapping(json.loads(record_bytes))
    if strings(data["condition"]) != CONDITION:
        raise ValueError("unsupported tool/index/platform/cache condition")
    declarations = strings(data["declarations"])
    if declarations.keys() != DECLARATIONS:
        raise ValueError("incomplete dependency declarations")
    for name, sha in declarations.items():
        if digest(regular(repository, name)) != sha:
            raise ValueError(f"stale dependency declaration: {name}")
    evidence = strings(data["evidence"])
    if not evidence or not data.get("derivation"):
        raise ValueError("missing reviewed preparation evidence/derivation")
    for name, sha in evidence.items():
        if digest(regular(record.parent, name)) != sha:
            raise ValueError(f"changed preparation evidence: {name}")
    files, links = strings(data["files"]), strings(data["links"])
    declared = packages(data["packages"])
    allowed: set[str] = set()
    for package in declared:
        allowed.update(package_entries(cache, package, files, links))
    if allowed != files.keys() or {p.wheel for p in declared} != links.keys():
        raise ValueError("inventory contains undeclared entries")
    for name, sha in files.items():
        if digest(regular(cache, name)) != sha:
            raise ValueError(f"changed selected file: {name}")
    for name, target in links.items():
        link = cache / relative(name)
        if link.parent.is_symlink() or not link.is_symlink():
            raise ValueError(f"missing wheel link: {name}")
        if link.readlink().as_posix() != target or not link.resolve().is_relative_to(
            cache.resolve()
        ):
            raise ValueError(f"external or changed link: {name}")
    return Selection(files, links, declared, expected)


def main() -> int:
    """Write selection or retained failure evidence into a new destination.

    Returns:
        Zero on success, one on recoverable selection failure.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cache", "record", "expected", "destination"):
        parser.add_argument(f"--{name}", required=True)
    args = parser.parse_args()
    if any(
        not getattr(args, name)
        for name in ("cache", "record", "expected", "destination")
    ):
        parser.error("cache, record, expected and destination must be nonempty")
    destination = Path(args.destination)
    if destination.resolve().is_relative_to(Path(args.cache).resolve()):
        sys.stderr.write("selection destination must be outside the input cache\n")
        return 1
    try:
        destination.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        sys.stderr.write(f"selection destination must be new: {exc}\n")
        return 1
    try:
        result = select(Path(args.cache), Path(args.record), args.expected, Path.cwd())
        output = {
            "files": result.files,
            "links": result.links,
            "packages": [asdict(p) for p in result.packages],
            "preparation_sha256": result.preparation_sha256,
            "condition": CONDITION,
        }
        (destination / "selection.json").write_text(json.dumps(output, indent=2) + "\n")
    except (ValueError, OSError, KeyError) as exc:
        message = (
            f"registry selection failed: {exc}; "
            "retain destination and reprepare/review inputs"
        )
        (destination / "failure.txt").write_text(message + "\n")
        sys.stderr.write(message + "\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
