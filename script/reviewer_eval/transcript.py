# SPDX-License-Identifier: Apache-2.0
"""Conservative extraction from one completed Codex JSONL turn."""

import json


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicate keys at every JSON nesting level.

    Returns:
        The decoded object.

    Raises:
        ValueError: A key is duplicated.
    """
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(raw: bytes) -> object:
    """Decode JSON with unique keys and standard numeric values.

    Returns:
        The decoded value.
    """

    def reject_constant(value: str) -> None:
        raise ValueError(f"invalid JSON constant: {value}")

    return json.loads(
        raw, object_pairs_hook=unique_object, parse_constant=reject_constant
    )


def extract_response(raw: bytes) -> tuple[str, bytes]:
    """Extract exactly one agent message from a single successful turn.

    Reasoning metadata is accepted only as completed reasoning items with string
    IDs and text. Other item kinds, including tool activity, are rejected.

    Returns:
        Thread identity and exact response bytes.

    Raises:
        ValueError: The transcript is malformed, ambiguous, or unsupported.
    """
    phase = 0
    response: str | None = None
    thread_id = ""
    for line in raw.splitlines():
        event = parse_json(line)
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise ValueError("invalid JSONL event")
        phase, response, thread_id = _advance(event, phase, response, thread_id)
    if phase != 3 or response is None:
        raise ValueError("JSONL turn is incomplete")
    try:
        encoded = response.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("agent message is not valid UTF-8") from exc
    return thread_id, encoded


def _advance(
    event: dict[str, object], phase: int, response: str | None, thread_id: str
) -> tuple[int, str | None, str]:
    kind = event["type"]
    if kind == "thread.started" and phase == 0:
        identity = event.get("thread_id")
        if not isinstance(identity, str) or not identity:
            raise ValueError("invalid thread identity")
        return 1, response, identity
    if kind == "turn.started" and phase == 1:
        return 2, response, thread_id
    if kind == "item.completed" and phase == 2:
        return phase, _item(event.get("item"), response), thread_id
    if kind == "turn.completed" and phase == 2 and response is not None:
        return 3, response, thread_id
    raise ValueError(f"unexpected JSONL event or lifecycle: {kind}")


def _item(item: object, response: str | None) -> str | None:
    if not isinstance(item, dict) or not isinstance(item.get("id"), str):
        raise ValueError("invalid completed item")
    if not item["id"] or not isinstance(item.get("text"), str):
        raise ValueError("invalid completed item content")
    if item.get("type") == "reasoning" and response is None:
        return None
    if item.get("type") != "agent_message" or response is not None:
        raise ValueError("unsupported or conflicting completed item")
    return item["text"]
