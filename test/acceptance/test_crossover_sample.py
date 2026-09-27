# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

import json
from pathlib import Path
import subprocess

import pytest


def test_crossover_sample_cli_run(tmp_path: Path):
    """Should execute example strategy with sample data via CLI."""

    output = tmp_path / "output.json"

    result = subprocess.run(
        [
            "uv",
            "run",
            "ataraxia",
            "-s",
            "example/crossover.py",
            "-d",
            "sample",
            "-o",
            output.resolve(),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == (
        "Aggregated backtest results:\nRealized PnL   = 40\nUnrealized PnL = 0\n"
    )

    results = json.loads(output.read_text())
    assert len(results) == 2

    results_by_shard = {result["shard_path"]: result for result in results}

    assert set(results_by_shard) == {
        str(Path("sample/nq_15m_2026_07_19.csv").resolve()),
        str(Path("sample/nq_15m_2026_07_20.csv").resolve()),
    }
    assert {result["strategy_path"] for result in results} == {
        str(Path("example/crossover.py").resolve())
    }
    assert {
        shard_path: result["account"] for shard_path, result in results_by_shard.items()
    } == {
        str(Path("sample/nq_15m_2026_07_19.csv").resolve()): {
            "pnl": 10,
            "unrealized_pnl": 0,
        },
        str(Path("sample/nq_15m_2026_07_20.csv").resolve()): {
            "pnl": 30,
            "unrealized_pnl": 0,
        },
    }
    assert {
        shard_path: [
            (position["side"], position["closing_level"], position["closing_pnl"])
            for position in result["closed_positions"]
        ]
        for shard_path, result in results_by_shard.items()
    } == {
        str(Path("sample/nq_15m_2026_07_19.csv").resolve()): [
            ("sell", 64926, 30),
            ("buy", 64608, -20),
        ],
        str(Path("sample/nq_15m_2026_07_20.csv").resolve()): [("buy", 64480, 30)],
    }
    assert all(result["open_positions"] == [] for result in results)


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
