# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Command line interface module."""

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from ataraxia.backtest import backtest_dir
from ataraxia.broker import BrokerReturn


def display_results(results: Sequence[BrokerReturn]) -> None:
    """Display broker results."""
    accounts_sum = sum(x["account"] for x in results)

    if accounts_sum == 0:
        print("No backtest completed, check params and output file", file=sys.stderr)
        sys.exit(1)

    print("Aggregated backtest results:")
    print(f"Realized PnL   = {accounts_sum.pnl}")
    print(f"Unrealized PnL = {accounts_sum.unrealized_pnl}")


def save_results(results: Sequence[BrokerReturn], to_file: Path) -> None:
    """Save results with details in to_file."""
    ...


def main() -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog=Path(sys.argv[0]).stem,
        description="Massively parallelized backtest orchestrator",
    )

    parser.add_argument("shard_dir", type=Path)
    parser.add_argument("strategy", type=Path)
    parser.add_argument("--output", type=Path, default="results.json")

    args = parser.parse_args()

    strategy: Path = args.strategy
    shard_dir: Path = args.shard_dir

    results = backtest_dir(strategy, shard_dir)

    display_results(results)
    save_results(results, args.output)
