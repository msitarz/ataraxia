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


def validate_package_layout(package: Package, links: dict[str, str]) -> None:
    """Require a supported declared wheel and its lexical archive association.

    Raises:
        ValueError: If root, origin, name, wheel, archive or link contradicts layout.
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


@dataclass(frozen=True)
class PackagePayload:
    """Complete allowed entries and the sole reviewed top-level METADATA path."""

    entries: frozenset[str]
    metadata_path: str
    payload: frozenset[str]


def package_payload(package: Package, files: dict[str, str]) -> PackagePayload:
    """Calculate complete payload/resolver entries and require derivation.

    Returns:
        Allowed entries and the METADATA path to observe separately.

    Raises:
        ValueError: If payload, resolver metadata or reviewed derivation is absent.
    """
    root, name, wheel, archive = (
        package.root,
        package.name,
        package.wheel,
        package.archive,
    )
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
    return PackagePayload(
        frozenset(payload | metadata), metadata_files[0], frozenset(payload)
    )


def validate_payload_metadata(
    package: Package, metadata_text: str, payload: frozenset[str]
) -> None:
    """Check observed METADATA and reject local-source or environment entries.

    Raises:
        ValueError: If METADATA contradicts provenance or payload contains local inputs.
    """
    name, version = package.name, package.version
    info = Parser().parsestr(metadata_text)
    normalized = re.sub(r"[-_.]+", "-", info.get("Name", "")).lower()
    if normalized != name or info.get("Version") != version:
        raise ValueError("payload METADATA contradicts preparation")
    if any(p.endswith(("/direct_url.json", "/pyvenv.cfg")) for p in payload):
        raise ValueError("local-source or environment payload")


def package_entries(
    cache: Path, package: Package, files: dict[str, str], links: dict[str, str]
) -> set[str]:
    """Observe one wheel's METADATA and compose pure package validation.

    Returns:
        The allowed file entries for this wheel.

    Validation propagates ValueError for contradictory declarations or layouts.
    """
    validate_package_layout(package, links)
    payload = package_payload(package, files)
    metadata_text = regular(cache, payload.metadata_path).read_text()
    validate_payload_metadata(package, metadata_text, payload.payload)
    return set(payload.entries)


def validate_digest(actual: str, expected: str, diagnostic: str) -> None:
    """Require equality to a separately supplied digest.

    Raises:
        ValueError: If digests differ, using the caller's contextual diagnostic.
    """
    if actual != expected:
        raise ValueError(diagnostic)


def accepted_preparation(record_bytes: bytes, expected: str) -> dict[str, object]:
    """Bind parsing and supported condition to the exact accepted record bytes.

    Returns:
        The checked JSON preparation object.

    Raises:
        ValueError: If acceptance or the supported condition differs.
    """
    diagnostic = "preparation digest differs from external acceptance"
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError(diagnostic)
    validate_digest(hashlib.sha256(record_bytes).hexdigest(), expected, diagnostic)
    data = mapping(json.loads(record_bytes))
    if strings(data["condition"]) != CONDITION:
        raise ValueError("unsupported tool/index/platform/cache condition")
    return data


def dependency_declarations(value: object) -> dict[str, str]:
    """Require the complete dependency declaration inventory.

    Returns:
        Checked declaration digests.

    Raises:
        ValueError: If declaration keys or digest value types are unsupported.
    """
    declarations = strings(value)
    if declarations.keys() != DECLARATIONS:
        raise ValueError("incomplete dependency declarations")
    return declarations


def preparation_evidence(value: object, derivation: object) -> dict[str, str]:
    """Require preparation evidence and a derivation description.

    Returns:
        Checked evidence digests.

    Raises:
        ValueError: If evidence or derivation is absent.
    """
    evidence = strings(value)
    if not evidence or not derivation:
        raise ValueError("missing reviewed preparation evidence/derivation")
    return evidence


def validate_selected_inventory(
    files: dict[str, str],
    links: dict[str, str],
    declared: tuple[Package, ...],
    allowed: set[str],
) -> None:
    """Require selected files and links to equal the declared package union.

    Raises:
        ValueError: If any selected entry is undeclared or incomplete.
    """
    if allowed != files.keys() or {p.wheel for p in declared} != links.keys():
        raise ValueError("inventory contains undeclared entries")


def validate_wheel_link(
    name: str,
    target: str,
    actual_target: str | None,
    parent_linked: bool,
    contained: bool,
) -> None:
    """Validate an observed wheel link without accessing the filesystem.

    Raises:
        ValueError: If the wheel link is missing, changed or external.
    """
    if parent_linked or actual_target is None:
        raise ValueError(f"missing wheel link: {name}")
    if actual_target != target or not contained:
        raise ValueError(f"external or changed link: {name}")


def check_file_digests(root: Path, inventory: dict[str, str], reason: str) -> None:
    """Observe regular inventory files and validate their digests in input order.

    Propagates ValueError for unsafe files or contextual digest disagreement.
    """
    for name, expected in inventory.items():
        validate_digest(digest(regular(root, name)), expected, f"{reason}: {name}")


def check_filesystem_wheel_link(cache: Path, name: str, target: str) -> None:
    """Observe one wheel link with ordered short-circuit filesystem checks.

    Propagates ValueError for missing, linked-parent, changed or external entries.
    """
    link = cache / relative(name)
    parent_linked = link.parent.is_symlink()
    actual_target = (
        link.readlink().as_posix() if not parent_linked and link.is_symlink() else None
    )
    contained = (
        link.resolve().is_relative_to(cache.resolve())
        if actual_target is not None and actual_target == target
        else False
    )
    validate_wheel_link(
        name,
        target,
        actual_target,
        parent_linked,
        contained,
    )


def select(cache: Path, record: Path, expected: str, repository: Path) -> Selection:
    """Validate an externally accepted preparation record without modifying cache.

    The caller must obtain expected from independent review, not from the record.
    Hash validation preserves that provenance; it does not authenticate downloads.

    Returns:
        Selected entries with provenance bound to the preparation digest.

    Validation propagates ValueError for contradictory preparation or cache entries.
    """
    record_bytes = record.read_bytes()
    data = accepted_preparation(record_bytes, expected)
    declarations = dependency_declarations(data["declarations"])
    check_file_digests(repository, declarations, "stale dependency declaration")
    evidence = preparation_evidence(data["evidence"], data.get("derivation"))
    check_file_digests(record.parent, evidence, "changed preparation evidence")
    files, links = strings(data["files"]), strings(data["links"])
    declared = packages(data["packages"])
    allowed: set[str] = set()
    for package in declared:
        allowed.update(package_entries(cache, package, files, links))
    validate_selected_inventory(files, links, declared, allowed)
    check_file_digests(cache, files, "changed selected file")
    for name, target in links.items():
        check_filesystem_wheel_link(cache, name, target)
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
