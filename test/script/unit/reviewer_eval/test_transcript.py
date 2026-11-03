# SPDX-License-Identifier: Apache-2.0
"""Exercise the supported saved Codex turn lifecycle."""

import json

import pytest

from script.reviewer_eval.transcript import extract_response


def encoded(events: list[dict[str, object]]) -> bytes:
    """Serialize synthetic events as JSONL."""
    return b"".join(json.dumps(event).encode() + b"\n" for event in events)


def events() -> list[dict[str, object]]:
    """Return a complete synthetic turn."""
    return [
        {"type": "thread.started", "thread_id": "thread"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {"type": "agent_message", "id": "a", "text": "{}"},
        },
        {"type": "turn.completed"},
    ]


def test_reasoning_and_opaque_extensions_are_accepted() -> None:
    # Given
    records = events()
    records.insert(
        2,
        {
            "type": "item.completed",
            "item": {"type": "reasoning", "id": "r", "text": "thought", "future": 7},
        },
    )
    records[-1]["usage"] = {"unknown": [1, 2]}

    # When
    result = extract_response(encoded(records))

    # Then
    assert result == ("thread", b"{}")


@pytest.mark.parametrize(
    "records",
    [
        events()[:-1],
        [*events(), {"type": "turn.completed"}],
        [*events()[:2], {"type": "turn.failed"}],
        [
            *events()[:2],
            {
                "type": "item.completed",
                "item": {"type": "command_execution", "id": "x", "text": ""},
            },
            *events()[2:],
        ],
        events()[:3] + events()[2:],
        [
            *events()[:2],
            {
                "type": "item.completed",
                "item": {"type": "reasoning", "id": "r", "text": 2},
            },
            *events()[2:],
        ],
    ],
    ids=[
        "missing-terminal",
        "extra-terminal",
        "failed",
        "tool",
        "two-messages",
        "bad-reasoning",
    ],
)
def test_unsupported_or_ambiguous_turn_is_rejected(
    records: list[dict[str, object]],
) -> None:
    # Given
    raw = encoded(records)

    # When / Then
    with pytest.raises(ValueError):
        extract_response(raw)


def test_duplicate_event_keys_are_rejected() -> None:
    # Given
    raw = b'{"type":"thread.started","type":"turn.started","thread_id":"x"}\n'

    # When / Then
    with pytest.raises(ValueError, match="duplicate JSON key"):
        extract_response(raw)


def test_unpaired_surrogate_in_message_is_rejected() -> None:
    # Given
    records = events()
    records[2] = {
        "type": "item.completed",
        "item": {"type": "agent_message", "id": "a", "text": "\ud800"},
    }

    # When / Then
    with pytest.raises(ValueError, match="UTF-8"):
        extract_response(encoded(records))
