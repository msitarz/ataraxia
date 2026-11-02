# SPDX-License-Identifier: Apache-2.0
"""Strict version parsing for the reviewed Codex quota integration."""

from dataclasses import dataclass
import re


@dataclass(frozen=True, order=True)
class CodexVersion:
    """A stable three-component Codex CLI release."""

    major: int
    minor: int
    patch: int


MINIMUM_QUOTA_VERSION = CodexVersion(0, 164, 0)
_VERSION = re.compile(
    r"(?:codex-cli )?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
)


def supports_quota_version(value: str | None) -> bool:
    """Return whether a stable, well-formed version meets the quota minimum."""
    if value is None:
        return False
    match = _VERSION.fullmatch(value)
    if match is None:
        return False
    try:
        version = CodexVersion(*(int(part) for part in match.groups()))
    except ValueError:
        return False
    return version >= MINIMUM_QUOTA_VERSION
