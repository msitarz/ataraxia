# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Command line interface module."""

import argparse
from collections.abc import Sequence
from pathlib import Path
from pprint import pprint
import sys

from ataraxia.backtest import backtest_dir
from ataraxia.broker import BrokerReturn


def display_results(results: Sequence[BrokerReturn]) -> None:
    """Display broker results."""
    ...


def main() -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog=Path(sys.argv[0]).stem,
        description="Massively parallelized backtest orchestrator",
    )

    parser.add_argument("shard_dir", type=Path)
    parser.add_argument("strategy_file", type=Path)

    args = parser.parse_args()

    shard_dir: Path = args.shard_dir
    strategy_file: Path = args.strategy_file

    results = backtest_dir(strategy_file, shard_dir)

    pprint(results)
