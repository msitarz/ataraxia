# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

import subprocess

import pytest


@pytest.mark.parametrize("existing_output", [False, True])
@pytest.mark.parametrize(
    ("contents", "message"),
    [
        (None, "No backtest completed"),
        ("", "CSV file must contain a header"),
        ("timestamp,open,high,low,close,volume\n", "contains no bars"),
        ("wrong,header\n", "CSV file must contain a header"),
        (
            "timestamp,open,high,low,close,volume\n"
            "1,100,200,50,150,1\n2,invalid,200,50,150,1\n",
            "Invalid bar",
        ),
        ("timestamp,open,high,low,close,volume\n1,100\n", "Invalid bar"),
    ],
    ids=[
        "no-shards",
        "empty-file",
        "header-only",
        "bad-header",
        "bad-value",
        "short-row",
    ],
)
def test_cli_shard_failure_preserves_output(
    tmp_path, existing_output, contents, message
):
    shards = tmp_path / "shards"
    shards.mkdir()
    if contents is not None:
        (shards / "invalid.csv").write_text(contents)
    output = tmp_path / "output.json"
    previous = b'{"previous": "result"}\n'
    if existing_output:
        output.write_bytes(previous)

    result = subprocess.run(
        [
            "uv",
            "run",
            "--no-sync",
            "ataraxia",
            "-s",
            "example/crossover.py",
            "-d",
            str(shards),
            "-o",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert message in result.stderr
    if contents is not None:
        assert str(shards / "invalid.csv") in result.stderr
    if existing_output:
        assert output.read_bytes() == previous
    else:
        assert not output.exists()
