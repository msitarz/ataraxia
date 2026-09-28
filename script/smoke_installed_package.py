# SPDX-License-Identifier: Apache-2.0
"""Build a wheel and exercise its installed CLI outside the source checkout."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


def main() -> None:
    """Verify installation, the console entry point, and sample backtest results."""
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    # Prevent caller configuration from exposing checkout modules to the CLI.
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env.pop("VIRTUAL_ENV", None)
    with TemporaryDirectory(prefix="ataraxia-package-") as directory:
        workspace = Path(directory).resolve()
        subprocess.run(
            ["uv", "build", "--wheel", "--out-dir", str(workspace / "dist")],
            cwd=root,
            env=env,
            check=True,
            timeout=120,
        )
        (wheel,) = (workspace / "dist").glob("*.whl")
        venv = workspace / "venv"
        subprocess.run(
            ["uv", "venv", "--python", sys.executable, str(venv)],
            cwd=workspace,
            env=env,
            check=True,
            timeout=120,
        )
        subprocess.run(
            ["uv", "pip", "install", "--python", str(venv / "bin/python"), str(wheel)],
            cwd=workspace,
            env=env,
            check=True,
            timeout=120,
        )
        shutil.copy2(root / "example/crossover.py", workspace / "crossover.py")
        shutil.copytree(root / "sample", workspace / "sample")
        result = subprocess.run(
            [
                str(venv / "bin/ataraxia"),
                "--sink",
                "crossover.py",
                "--shards-dir",
                "sample",
                "--output",
                "results.json",
            ],
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
        assert result.stderr == "", result.stderr
        assert result.stdout == (
            "Aggregated backtest results:\nRealized PnL   = 40\nUnrealized PnL = 0\n"
        ), result.stdout
        results = json.loads((workspace / "results.json").read_text())
        assert len(results) == 2, results
        assert {Path(item["shard_path"]).name: item["account"] for item in results} == {
            "nq_15m_2026_07_19.csv": {"pnl": 10, "unrealized_pnl": 0},
            "nq_15m_2026_07_20.csv": {"pnl": 30, "unrealized_pnl": 0},
        }, results


if __name__ == "__main__":
    main()
