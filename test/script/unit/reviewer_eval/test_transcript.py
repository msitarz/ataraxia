# SPDX-License-Identifier: Apache-2.0
"""Exercise the supported saved Codex turn lifecycle."""

from collections.abc import Callable
import json

import pytest

from script.reviewer_eval.transcript import extract_response, parse_json


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


@pytest.mark.parametrize(
    "decoder", [parse_json, extract_response], ids=["json", "jsonl"]
)
def test_decoder_limit_is_reported_as_invalid(
    decoder: Callable[[bytes], object],
) -> None:
    # Given
    raw = b"[" * 400_000 + b"]" * 400_000

    # When / Then
    with pytest.raises(
        ValueError, match="invalid JSON: nesting exceeds decoder limit"
    ) as error:
        decoder(raw)
    assert isinstance(error.value.__cause__, RecursionError)


def test_invalid_json_encoding_is_reported_with_its_cause() -> None:
    # Given
    raw = b"\xff"

    # When / Then
    with pytest.raises(ValueError, match="invalid Unicode encoding") as error:
        parse_json(raw)
    assert isinstance(error.value.__cause__, UnicodeDecodeError)


def disabled_host_notice(ident: str = "notice") -> dict[str, object]:
    """Return the known startup notice as a synthetic event."""
    return {
        "type": "item.completed",
        "item": {
            "type": "error",
            "id": ident,
            "message": (
                "Code Mode is unavailable because code-mode host is disabled. "
                "Code mode will fail closed; enable "
                "`features.code_mode_host` and install "
                "`codex-code-mode-host`."
            ),
        },
    }


def test_disabled_host_notice_before_turn_is_accepted() -> None:
    # Given
    records = [events()[0], disabled_host_notice(), *events()[1:]]

    # When
    result = extract_response(encoded(records))

    # Then
    assert result == ("thread", b"{}")


@pytest.mark.parametrize(
    "records",
    [
        [
            events()[0],
            {
                "type": "item.completed",
                "item": {"type": "error", "id": "x", "message": "other"},
            },
            *events()[1:],
        ],
        [events()[0], disabled_host_notice(""), *events()[1:]],
        [*events()[:2], disabled_host_notice(), *events()[2:]],
        [events()[0], disabled_host_notice(), disabled_host_notice(), *events()[1:]],
        [events()[0], disabled_host_notice(), {"type": "turn.failed"}],
        [events()[0], disabled_host_notice()],
    ],
    ids=["other-error", "invalid-id", "after-turn", "repeated", "failed", "incomplete"],
)
def test_unrecognized_notice_lifecycle_is_rejected(
    records: list[dict[str, object]],
) -> None:
    # Given
    raw = encoded(records)

    # When / Then
    with pytest.raises(ValueError):
        extract_response(raw)
