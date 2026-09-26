# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Command line interface module."""

import argparse
from collections.abc import Sequence
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import TypeGuard

from ataraxia.backtest import backtest_dir
from ataraxia.broker import Account, BrokerReturn, Position


def _is_broker_results(results: Sequence[object]) -> TypeGuard[Sequence[BrokerReturn]]:
    """Return whether every result has the broker fields required by the CLI."""
    for result in results:
        if not isinstance(result, dict) or not isinstance(
            result.get("account"), Account
        ):
            return False
        for key in ("open_positions", "closed_positions"):
            positions = result.get(key)
            if (
                not isinstance(positions, Sequence)
                or isinstance(positions, (str, bytes, bytearray))
                or not all(isinstance(position, Position) for position in positions)
            ):
                return False
    return True


def display_results(results: Sequence[BrokerReturn]) -> None:
    """Display broker results."""
    accounts_sum = sum(x["account"] for x in results)

    if isinstance(accounts_sum, Account):
        print("Aggregated backtest results:")
        print(f"Realized PnL   = {accounts_sum.pnl}")
        print(f"Unrealized PnL = {accounts_sum.unrealized_pnl}")


def save_results(results: Sequence[BrokerReturn], to_file: Path) -> None:
    """Save results with details in to_file."""
    with to_file.open("w") as fp:
        json.dump(results, fp, indent=2, default=lambda obj: asdict(obj))


def main() -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog=Path(sys.argv[0]).stem,
        description="Massively parallelized backtest orchestrator",
    )

    parser.add_argument(
        "-s",
        "--sink",
        type=Path,
        required=True,
        help="Path to Python file with graph sink",
    )
    parser.add_argument(
        "-d",
        "--shards-dir",
        type=Path,
        required=True,
        help="Path to directory with shard files to backtest",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default="results.json",
        help="Path to output file with results",
    )

    args = parser.parse_args()

    sink: Path = args.sink
    shards_dir: Path = args.shards_dir

    results = backtest_dir(sink, shards_dir)

    if not results:
        print("No backtest completed, check params and output file", file=sys.stderr)
        sys.exit(1)

    if not _is_broker_results(results):
        print(
            "CLI requires broker results: an Account and open/closed Position "
            "sequences. Use the Python backtest API for other sink values.",
            file=sys.stderr,
        )
        sys.exit(1)

    display_results(results)
    save_results(results, args.output)
