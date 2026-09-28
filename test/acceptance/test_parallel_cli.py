# SPDX-License-Identifier: Apache-2.0
from contextlib import suppress
import json
import os
from pathlib import Path
import signal
import subprocess
import time

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMMAND = ROOT / ".venv/bin/ataraxia"
HEADER = "timestamp,open,high,low,close,volume\n"


@pytest.mark.parametrize("options", [[], ["--parallel", "2"]])
def test_mixed_failures_save_and_continue(tmp_path, options):
    shards = tmp_path / "shards"
    shards.mkdir()
    (shards / "bad.csv").write_text("bad\n")
    (shards / "directory").mkdir()
    (shards / "good.csv").write_text(
        (ROOT / "sample/nq_15m_2026_07_19.csv").read_text()
    )
    output = tmp_path / "out.json"
    output.write_text("previous")
    result = subprocess.run(
        [
            str(COMMAND),
            "-s",
            str(ROOT / "example/crossover.py"),
            "-d",
            str(shards),
            "-o",
            str(output),
            *options,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 1
    assert "Realized PnL   = 10" in result.stdout
    assert "2 shard(s) failed" in result.stderr
    assert str(output) in result.stderr
    outcomes = json.loads(output.read_text())
    assert len(outcomes) == 3
    assert sum(item["status"] == "success" for item in outcomes) == 1
    assert all("result" not in item for item in outcomes if item["status"] == "error")


def hanging_strategy(tmp_path):
    strategy = tmp_path / "strategy.py"
    strategy.write_text("""
from dataclasses import dataclass
from pathlib import Path
import os
import time
from ataraxia.broker import Account

class Runner:
    def __call__(self, item):
        pidfile = Path(__file__).with_name(f'{item.timestamp}.pid')
        temporary = pidfile.with_suffix('.tmp')
        temporary.write_text(str(os.getpid()))
        temporary.replace(pidfile)
        if item.timestamp == 1:
            while True:
                time.sleep(.01)
        return {'account': Account(pnl=item.timestamp),
                'open_positions': [], 'closed_positions': []}

@dataclass(frozen=True)
class Strategy:
    source: object
    def deps(self):
        return {'item': self.source}
    def sources(self):
        return (self.source,)
    def consumer(self):
        return None
    def factory(self):
        return Runner()

__sink__ = Strategy
""")
    return strategy


def test_cli_timeout_saved_and_replacement_succeeds(tmp_path):
    strategy = hanging_strategy(tmp_path)
    shards = tmp_path / "shards"
    shards.mkdir()
    (shards / "first.csv").touch()
    (shards / "second.csv").touch()
    first, second = tuple(shards.iterdir())
    first.write_text(HEADER + "1,1,1,1,1,1\n")
    second.write_text(HEADER + "2,1,1,1,1,1\n")
    output = tmp_path / "out.json"
    try:
        result = subprocess.run(
            [
                str(COMMAND),
                "-s",
                str(strategy),
                "-d",
                str(shards),
                "-o",
                str(output),
                "--parallel",
                "1",
                "--shard-timeout",
                ".5",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        for pidfile in tmp_path.glob("*.pid"):
            with suppress(ProcessLookupError):
                os.kill(int(pidfile.read_text()), signal.SIGKILL)
        raise
    assert result.returncode == 1, result.stderr
    outcomes = {
        Path(item["shard_path"]).name: item for item in json.loads(output.read_text())
    }
    assert outcomes[first.name]["error"]["kind"] == "timeout"
    assert outcomes[second.name]["status"] == "success"
    assert "Realized PnL   = 2" in result.stdout
    assert (tmp_path / "1.pid").read_text() != (tmp_path / "2.pid").read_text()
    for pidfile in tmp_path.glob("*.pid"):
        with pytest.raises(ProcessLookupError):
            os.kill(int(pidfile.read_text()), 0)


def test_interrupt_cleans_workers_and_preserves_output(tmp_path):
    strategy = hanging_strategy(tmp_path)
    shards = tmp_path / "shards"
    shards.mkdir()
    (shards / "hang.csv").write_text(HEADER + "1,1,1,1,1,1\n")
    output = tmp_path / "out.json"
    output.write_text("previous")
    process = subprocess.Popen(
        [
            str(COMMAND),
            "-s",
            str(strategy),
            "-d",
            str(shards),
            "-o",
            str(output),
            "--parallel",
            "1",
            "--shard-timeout",
            "10",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 5
        while not (tmp_path / "1.pid").exists():
            assert time.monotonic() < deadline
            assert process.poll() is None
            time.sleep(0.01)
        process.send_signal(signal.SIGINT)
        process.communicate(timeout=5)
        assert process.returncode != 0
        assert output.read_text() == "previous"
        with pytest.raises(ProcessLookupError):
            os.kill(int((tmp_path / "1.pid").read_text()), 0)
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
        pidfile = tmp_path / "1.pid"
        if pidfile.exists():
            with suppress(ProcessLookupError):
                os.kill(int(pidfile.read_text()), signal.SIGKILL)


@pytest.mark.parametrize("options", [[], ["--parallel", "1"]])
def test_discovery_failure_preserves_output(tmp_path, options):
    output = tmp_path / "out.json"
    output.write_text("previous")
    result = subprocess.run(
        [
            str(COMMAND),
            "-s",
            str(ROOT / "example/crossover.py"),
            "-d",
            str(tmp_path / "missing"),
            "-o",
            str(output),
            *options,
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert output.read_text() == "previous"


@pytest.mark.parametrize("options", [[], ["--parallel", "2"]])
@pytest.mark.parametrize("contents", ["", "raise ValueError('import failed')\n"])
def test_strategy_errors_are_saved_in_both_modes(tmp_path, options, contents):
    strategy = tmp_path / "strategy.py"
    strategy.write_text(contents)
    output = tmp_path / "out.json"
    result = subprocess.run(
        [
            str(COMMAND),
            "-s",
            str(strategy),
            "-d",
            str(ROOT / "sample"),
            "-o",
            str(output),
            *options,
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "2 shard(s) failed" in result.stderr
    outcomes = json.loads(output.read_text())
    assert len(outcomes) == 2
    assert all(item["error"]["kind"] == "exception" for item in outcomes)
    assert all("result" not in item for item in outcomes)


@pytest.mark.parametrize(
    "options",
    [
        ["--parallel", "0"],
        ["--shard-timeout", "1"],
        ["--parallel", "1", "--shard-timeout", "nan"],
    ],
)
def test_console_invalid_arguments_preserve_output(tmp_path, options):
    output = tmp_path / "out.json"
    output.write_text("previous")
    result = subprocess.run(
        [
            str(COMMAND),
            "-s",
            str(ROOT / "example/crossover.py"),
            "-d",
            str(ROOT / "sample"),
            "-o",
            str(output),
            *options,
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert output.read_text() == "previous"
