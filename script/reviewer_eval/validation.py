# SPDX-License-Identifier: Apache-2.0
"""Validate a model response against supplied review inputs.

This boundary accepts response JSON bytes, not a CLI transcript. The caller
supplies the rule IDs and original source bytes associated with the call.
"""

from collections.abc import Mapping
from dataclasses import dataclass
import json
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Nonempty = Annotated[str, Field(min_length=1)]
PositiveLine = Annotated[int, Field(ge=1)]


class Finding(BaseModel):
    """One schema-valid finding, before owner adjudication."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    rule_id: Literal["R1", "R3", "R4"]
    file_id: Nonempty
    start_line: PositiveLine
    end_line: PositiveLine
    quote: Nonempty
    explanation: Nonempty
    consequence: Nonempty
    severity: Literal["critical", "major", "minor"]
    corrections: tuple[Nonempty, ...] = Field(default=(), strict=False)


@dataclass(frozen=True)
class ValidatedResponse:
    """A valid response; incomplete findings must not receive quality credit."""

    complete: bool
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class InvalidResponse:
    """A rejected response and an actionable explanation."""

    diagnostic: str


def validate_response(
    raw: bytes, *, allowed_rules: frozenset[str], sources: Mapping[str, bytes]
) -> ValidatedResponse | InvalidResponse:
    """Validate raw JSON and its findings against caller-supplied source.

    For example, a complete response with an empty findings array is valid;
    an incomplete response retains its findings but cannot earn quality credit.
    Source lines retain original newline bytes for exact quote matching.

    Returns:
        A validated response or an invalid response with a diagnostic.
    """
    try:
        decoded = raw.decode("utf-8")
        data = json.loads(
            decoded, object_pairs_hook=_unique_object, parse_constant=_reject_constant
        )
        response = _Response.model_validate(data)
    except (UnicodeDecodeError, ValueError) as exc:
        return InvalidResponse(f"invalid response JSON or schema: {exc}")
    for index, finding in enumerate(response.findings):
        problem = _source_problem(finding, allowed_rules, sources)
        if problem is not None:
            return InvalidResponse(f"findings[{index}]: {problem}")
    return ValidatedResponse(response.complete, tuple(response.findings))


class _Response(BaseModel):
    """The schema-valid response envelope."""

    model_config = ConfigDict(extra="forbid", strict=True)

    complete: bool
    findings: list[Finding]


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build a JSON object.

    Returns:
        The object with its original keys and values.

    Raises:
        ValueError: If a key occurs more than once.
    """
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    """Reject a non-standard numeric constant.

    Raises:
        ValueError: Always, because the constant is not JSON.
    """
    raise ValueError(f"invalid JSON constant: {value}")


def _source_problem(
    finding: Finding, allowed_rules: frozenset[str], sources: Mapping[str, bytes]
) -> str | None:
    """Check a schema-valid finding against the supplied inputs.

    Returns:
        A diagnostic if the finding is invalid, otherwise None.
    """
    if finding.rule_id not in allowed_rules:
        return f"rule_id {finding.rule_id!r} was not supplied"
    if finding.file_id not in sources:
        return f"file_id {finding.file_id!r} was not supplied"
    if finding.start_line > finding.end_line:
        return "start_line exceeds end_line"
    # LF separates lines; keep the original bytes, including CR in CRLF.
    source = sources[finding.file_id]
    lines = re.findall(rb"[^\n]*\n|[^\n]+", source)
    if finding.end_line > len(lines):
        return f"end_line {finding.end_line} exceeds source line count {len(lines)}"
    span = b"".join(lines[finding.start_line - 1 : finding.end_line])
    try:
        quote = finding.quote.encode("utf-8")
    except UnicodeEncodeError:
        return "quote is not valid UTF-8"
    if quote not in span:
        return "quote does not match original source bytes within the claimed span"
    return None
