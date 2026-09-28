# SPDX-License-Identifier: Apache-2.0
from unittest.mock import MagicMock

import pytest

from ataraxia.broker import Account
from ataraxia.shard_pool import Receipt, Worker, assignment_outcome, run_shards
from ataraxia.shard_types import is_shard_outcome


@pytest.mark.parametrize("arrival", [14.99, 15, 15.01])
def test_deadline_race(arrival):
    request = {"strategy_path": "/s", "shard_path": "/d"}
    outcome = {
        **request,
        "status": "success",
        "result": {"account": Account(), "open_positions": [], "closed_positions": []},
    }
    worker = Worker(MagicMock(), MagicMock(), 1, request, 10)
    result = assignment_outcome(worker, Receipt(1, arrival, outcome), 15.1, 5)
    assert result["status"] == ("success" if arrival < 15 else "error")
    if arrival >= 15:
        assert result["error"]["kind"] == "timeout"
    assert assignment_outcome(Worker(MagicMock(), MagicMock()), None, 100, 5) is None


@pytest.mark.parametrize(
    ("size", "timeout"), [(0, 1), (1, 0), (1, float("nan")), (1, float("inf"))]
)
def test_invalid_configuration(size, timeout):
    with pytest.raises(ValueError):
        run_shards([], size, timeout, MagicMock())


@pytest.mark.parametrize(
    "value",
    [
        None,
        {},
        {"status": "success"},
        {"strategy_path": "/s", "shard_path": "/d", "status": "error", "error": None},
    ],
)
def test_invalid_outcome(value):
    assert not is_shard_outcome(value)


def test_startup_failure_consumes_each_assignment():
    from unittest.mock import patch

    inputs = [{"strategy_path": "/s", "shard_path": f"/d/{i}"} for i in range(3)]
    with patch(
        "ataraxia.shard_pool._start", side_effect=OSError("cannot spawn")
    ) as start:
        results = run_shards(inputs, 2, 1, MagicMock())
    assert start.call_count == 3
    assert [item["shard_path"] for item in results] == ["/d/0", "/d/1", "/d/2"]
    assert all(item["error"]["kind"] == "worker_failure" for item in results)


def test_late_receipt_cannot_be_attributed_to_replacement():
    from queue import Queue

    from ataraxia.shard_pool import _collect

    process = MagicMock()
    process.exitcode = None
    replacement = Worker(
        process, MagicMock(), 2, {"strategy_path": "/s", "shard_path": "/new"}, 100
    )
    events = Queue()
    events.put(
        Receipt(
            1,
            99,
            {
                "strategy_path": "/s",
                "shard_path": "/old",
                "status": "success",
                "result": {
                    "account": Account(),
                    "open_positions": [],
                    "closed_positions": [],
                },
            },
        )
    )
    from unittest.mock import patch

    results = []
    with patch("ataraxia.shard_pool.monotonic", return_value=101):
        _collect([replacement], events, 5, results)
    assert results == []
    assert replacement.request["shard_path"] == "/new"


def test_cleanup_attempts_every_owned_worker_and_reports_failure():
    from unittest.mock import patch

    from ataraxia.errors import SupervisorError
    from ataraxia.shard_pool import _cleanup

    with (
        patch(
            "ataraxia.shard_pool._retire", side_effect=[RuntimeError("bad"), None]
        ) as retire,
        pytest.raises(SupervisorError),
    ):
        _cleanup([MagicMock(), MagicMock()])
    assert retire.call_count == 2
