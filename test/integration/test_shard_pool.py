# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import subprocess
import sys

import pytest

PROBE = """
from pathlib import Path
import os
import time
import multiprocessing
from ataraxia.shard_pool import run_shards
from ataraxia.broker import Account

def operation(strategy, shard):
    root = Path(strategy)
    name = Path(shard).name
    pidfile = root / (name + '.pid')
    temporary = root / (name + '.tmp')
    temporary.write_text(str(os.getpid()))
    temporary.replace(pidfile)
    if name in ('fastvalid', 'valid'):
        (root / (name + '.done')).touch()
    if name == 'hang':
        while True:
            time.sleep(.01)
    if name == 'crash':
        os._exit(7)
    if name == 'unaffected':
        while not (root / 'hang.pid').exists():
            time.sleep(.01)
        pid = int((root / 'hang.pid').read_text())
        while True:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(.005)
    if name in ('slow', 'fast'):
        (root / (name + '.ready')).touch()
        other = 'fast' if name == 'slow' else 'slow'
        while not (root / (other + '.ready')).exists():
            time.sleep(.01)
        if name == 'slow':
            while not (root / 'fast.done').exists():
                time.sleep(.01)
            time.sleep(.1)
        else:
            (root / 'fast.done').touch()
    if name == 'exception':
        from ataraxia.backtest import backtest_shard
        outcome = backtest_shard(root / 'broken.py', shard)
        outcome['strategy_path'] = strategy
        return outcome
    if name == 'large':
        # A large formatted diagnostic tests transfer independently of broker data.
        return {'strategy_path': strategy, 'shard_path': shard, 'status': 'error',
                'error': {'kind': 'exception', 'type': 'builtins.ValueError',
                          'message': 'large', 'traceback': 'x' * 20000000}}
    return {'strategy_path': strategy, 'shard_path': shard, 'status': 'success',
            'result': {'account': Account(),
                       'open_positions': [], 'closed_positions': []}}

def transfer_worker(channel, operation):
    import struct
    request = channel.recv()
    name = Path(request['shard_path']).name
    pidfile = Path(request['strategy_path']) / (name + '.pid')
    temporary = pidfile.with_suffix('.tmp')
    temporary.write_text(str(os.getpid()))
    temporary.replace(pidfile)
    if name in ('partial', 'partial_exit'):
        os.write(channel.fileno(), struct.pack('!i', 10000000) + b'partial')
        if name == 'partial_exit':
            os._exit(9)
        while True:
            time.sleep(.01)
    if name == 'invalid':
        channel.send({'status': 'nonsense'})
    else:
        channel.send(operation(request['strategy_path'], request['shard_path']))
    try:
        while True:
            request = channel.recv()
            channel.send(operation(request['strategy_path'], request['shard_path']))
    except EOFError:
        pass

if __name__ == '__main__':
    import json
    import sys
    from dataclasses import asdict
    root = Path(sys.argv[1])
    names = sys.argv[2].split(',')
    inputs = [{'strategy_path': str(root), 'shard_path': str(root / name)}
              for name in names]
    from unittest.mock import patch
    from ataraxia.shard_pool import _worker, _start, _launch, _collect
    starts = 0
    def staggered_start(operation):
        global starts
        starts += 1
        worker = _start(operation)
        if starts == 1:
            time.sleep(.2)
        return worker
    transfer = any(n in names for n in ('partial', 'partial_exit', 'invalid'))
    def delayed_launch(worker):
        if Path(worker.request['shard_path']).name == 'startup':
            while not (root / 'fastvalid.done').exists():
                time.sleep(.005)
            time.sleep(.3)
        _launch(worker)
    def parent_failure(*args):
        deadline = time.monotonic() + 3
        while not (root / 'hang.pid').exists():
            assert time.monotonic() < deadline
            time.sleep(.005)
        if 'interrupt' in names:
            raise KeyboardInterrupt()
        raise RuntimeError('parent bug')
    entry = transfer_worker if transfer else _worker
    start = staggered_start if 'unaffected' in names else _start
    launch = delayed_launch if 'startup' in names else _launch
    failing_parent = any(n in names for n in ('interrupt', 'parentbug'))
    collect = parent_failure if failing_parent else _collect
    with patch('ataraxia.shard_pool._worker', entry), \
         patch('ataraxia.shard_pool._start', start), \
         patch('ataraxia.shard_pool._launch', launch), \
         patch('ataraxia.shard_pool._collect', collect):
        try:
            outcomes = run_shards(
                inputs, int(sys.argv[3]), float(sys.argv[4]), operation)
        except (KeyboardInterrupt, RuntimeError) as exc:
            if not any(n in names for n in ('interrupt', 'parentbug')):
                raise
            outcomes = [{'parent_error': type(exc).__name__}]

    assert not multiprocessing.active_children()
    for name in names:
        pidfile = root / (name + '.pid')
        if pidfile.exists():
            try:
                os.kill(int(pidfile.read_text()), 0)
            except ProcessLookupError:
                pass
            else:
                raise AssertionError('child still alive')
    (root / 'out.json').write_text(json.dumps(outcomes, default=asdict))
"""


def probe(tmp_path, names, size, timeout=2):
    script = tmp_path / "probe.py"
    script.write_text(PROBE)
    import os

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path("src").resolve())
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                str(tmp_path),
                names,
                str(size),
                str(timeout),
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, result.stderr
        import json

        return json.loads((tmp_path / "out.json").read_text())
    finally:
        from contextlib import suppress
        import signal

        for pidfile in tmp_path.glob("*.pid"):
            with suppress(ProcessLookupError):
                os.kill(int(pidfile.read_text()), signal.SIGKILL)


def test_real_spawn_overlap_and_arrival(tmp_path):
    results = probe(tmp_path, "slow,fast", 2)
    assert [Path(item["shard_path"]).name for item in results] == ["fast", "slow"]
    assert all(item["status"] == "success" for item in results)


@pytest.mark.parametrize(
    ("name", "kind"), [("hang", "timeout"), ("crash", "worker_failure")]
)
def test_replacement_and_no_retry(tmp_path, name, kind):
    results = probe(tmp_path, f"{name},valid,next", 1, 0.5)
    assert results[0]["error"]["kind"] == kind
    assert [item["status"] for item in results[1:]] == ["success", "success"]
    assert (tmp_path / f"{name}.pid").read_text() != (
        tmp_path / "valid.pid"
    ).read_text()
    assert (tmp_path / "valid.pid").read_text() == (tmp_path / "next.pid").read_text()


def test_large_transfer_does_not_block_other_deadline(tmp_path):
    results = probe(tmp_path, "hang,large,valid", 2, 0.5)
    assert len(results) == 3
    assert {Path(item["shard_path"]).name: item["status"] for item in results} == {
        "hang": "error",
        "large": "error",
        "valid": "success",
    }
    assert (
        next(item for item in results if Path(item["shard_path"]).name == "hang")[
            "error"
        ]["kind"]
        == "timeout"
    )


def test_unpicklable_exception_retains_cause(tmp_path):
    (tmp_path / "broken.py").write_text("""
class Broken(Exception):
    def __init__(self):
        self.callback = lambda: None
        super().__init__('outer')
try:
    raise ValueError('original')
except ValueError as cause:
    raise Broken() from cause
""")
    results = probe(tmp_path, "exception,valid", 1)
    assert results[0]["error"]["kind"] == "exception"
    assert "original" in results[0]["error"]["traceback"]
    assert "direct cause" in results[0]["error"]["traceback"]
    assert results[1]["status"] == "success"


def test_partial_transfer_kill_preserves_other_channel_and_replacement(tmp_path):
    results = probe(tmp_path, "partial,fastvalid,valid", 2, 0.5)
    by_name = {Path(item["shard_path"]).name: item for item in results}
    assert by_name["partial"]["error"]["kind"] == "timeout"
    assert by_name["fastvalid"]["status"] == "success"
    assert by_name["valid"]["status"] == "success"


def test_timeout_preserves_unaffected_worker(tmp_path):
    results = probe(tmp_path, "hang,unaffected,valid", 2, 0.6)
    assert sum(item["status"] == "success" for item in results) == 2
    assert (tmp_path / "hang.pid").read_text() != (tmp_path / "valid.pid").read_text()


@pytest.mark.parametrize("name", ["partial_exit", "invalid"])
def test_incomplete_or_invalid_message_replaces_worker(tmp_path, name):
    results = probe(tmp_path, f"{name},valid", 1, 1)
    assert results[0]["error"]["kind"] == "worker_failure"
    assert results[1]["status"] == "success"


def test_startup_does_not_block_other_assignment(tmp_path):
    outcomes = probe(tmp_path, "startup,fastvalid", 2, 0.2)
    by_name = {Path(item["shard_path"]).name: item for item in outcomes}
    assert by_name["startup"]["error"]["kind"] == "timeout"
    assert by_name["fastvalid"]["status"] == "success"


@pytest.mark.parametrize("failure", ["interrupt", "parentbug"])
def test_parent_failure_cleans_active_workers(tmp_path, failure):
    outcomes = probe(tmp_path, f"hang,{failure}", 1, 2)
    assert outcomes == [
        {
            "parent_error": "KeyboardInterrupt"
            if failure == "interrupt"
            else "RuntimeError"
        }
    ]
