# SPDX-License-Identifier: Apache-2.0
"""Public argument parsing preserves matrix option order."""

from pathlib import Path

import pytest

from script.eval.model import DirectoryOption, SeparatorOption
from script.eval.options import parse_config


def test_options_preserve_order_across_other_flags() -> None:
    # Given
    argv = [
        "-d",
        "first",
        "-m",
        "a",
        "-s",
        r"\n",
        "-e",
        "low",
        "-d",
        "second",
        "-m",
        "a",
        "-n",
    ]

    # When
    config = parse_config(argv)

    # Then
    assert config.ordered_options == (
        DirectoryOption(position=0, path=Path("first")),
        SeparatorOption(position=1, value=r"\n"),
        DirectoryOption(position=2, path=Path("second")),
    )
    assert config.models == ("a", "a")
    assert config.efforts == ("low",)
    assert config.dry_run


@pytest.mark.parametrize(
    "extra",
    [["-s", "x"], ["-c", "0"], ["--capacity-retry-limit", "1"]],
    ids=["dangling-separator", "zero-concurrency", "missing-backoff"],
)
def test_invalid_arguments_are_rejected(extra: list[str]) -> None:
    # Given
    argv = ["-d", "context", "-m", "model", "-e", "low", "-n", *extra]

    # When
    with pytest.raises(SystemExit) as caught:
        parse_config(argv)

    # Then
    assert caught.value.code == 2
