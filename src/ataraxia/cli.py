# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Command line interface module."""

import argparse
from collections.abc import Sequence
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile

from ataraxia.backtest import BacktestShardReturn, backtest_dir
from ataraxia.broker import Account, BrokerReturn


def display_results(results: Sequence[BrokerReturn]) -> None:
    """Display broker results."""
    accounts_sum = sum(x["account"] for x in results)

    if isinstance(accounts_sum, Account):
        print("Aggregated backtest results:")
        print(f"Realized PnL   = {accounts_sum.pnl}")
        print(f"Unrealized PnL = {accounts_sum.unrealized_pnl}")


def save_results(results: Sequence[BacktestShardReturn], to_file: Path) -> None:
    """Save results with details in to_file."""
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(mode="w", dir=to_file.parent, delete=False) as fp:
            temporary = Path(fp.name)
            json.dump(results, fp, indent=2, default=lambda obj: asdict(obj))
        temporary.replace(to_file)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _positive_int(value: str) -> int:
    try:
        result = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Must be a positive integer") from exc
    if result <= 0:
        raise argparse.ArgumentTypeError("Must be a positive integer")
    return result


def _positive_seconds(value: str) -> float:
    try:
        result = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Must be finite positive seconds") from exc
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError("Must be finite positive seconds")
    return result


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

    parser.add_argument(
        "--parallel",
        nargs="?",
        type=_positive_int,
        const=os.process_cpu_count() or 1,
        default=None,
        help=(
            "Run in child processes; optional positive worker count "
            "(default: available processors)"
        ),
    )
    parser.add_argument(
        "--shard-timeout",
        type=_positive_seconds,
        default=None,
        help="Parallel assignment deadline in seconds, including startup (default: 5)",
    )
    args = parser.parse_args()
    if args.shard_timeout is not None and args.parallel is None:
        parser.error("--shard-timeout requires --parallel")

    sink: Path = args.sink
    shards_dir: Path = args.shards_dir

    results = backtest_dir(
        sink,
        shards_dir,
        parallel=args.parallel,
        shard_timeout=args.shard_timeout if args.shard_timeout is not None else 5.0,
    )

    if not results:
        print("No backtest completed, check params and output file", file=sys.stderr)
        sys.exit(1)

    successes = [item["result"] for item in results if item["status"] == "success"]
    save_results(results, args.output)
    if successes:
        display_results(successes)
    failures = len(results) - len(successes)
    if failures:
        print(
            f"{failures} shard(s) failed; diagnostics saved to {args.output}",
            file=sys.stderr,
        )
        sys.exit(1)
