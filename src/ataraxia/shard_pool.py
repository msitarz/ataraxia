# SPDX-License-Identifier: Apache-2.0
"""Bounded spawn workers with independent channels and assignment deadlines."""

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
import math
from multiprocessing import get_context
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from queue import Empty, Queue
from threading import Event, Lock, Thread
from time import monotonic

from ataraxia.errors import SupervisorError
from ataraxia.shard_types import (
    BacktestShardReturn,
    ShardFailure,
    ShardInput,
    is_shard_input,
    is_shard_outcome,
)

type ShardOperation = Callable[[str, str], BacktestShardReturn]


@dataclass(frozen=True)
class Receipt:
    """Record completion after receiving and validating an entire outcome."""

    assignment: int
    completed: float
    outcome: BacktestShardReturn | None
    failure: str | None = None


@dataclass
class Worker:
    """Own one process, channel, and active assignment at a time."""

    process: BaseProcess
    channel: Connection
    assignment: int = -1
    request: ShardInput | None = None
    started: float = 0.0
    reader: Thread | None = None
    child_channel: Connection | None = None
    launch_complete: Event = field(default_factory=Event)
    receipt_lock: Lock = field(default_factory=Lock)
    receipt: Receipt | None = None
    committed: bool = False


def _worker(channel: Connection, operation: ShardOperation) -> None:
    try:
        while True:
            request: object = channel.recv()
            if not is_shard_input(request) or set(request) != {
                "strategy_path",
                "shard_path",
            }:
                raise ValueError("Invalid shard input")
            channel.send(operation(request["strategy_path"], request["shard_path"]))
    except EOFError:
        return
    finally:
        channel.close()


def _exchange(worker: Worker, events: Queue[Receipt]) -> None:
    assignment = worker.assignment
    request = worker.request
    if request is None:
        raise SupervisorError("Cannot dispatch an idle worker")
    try:
        _launch(worker)
        worker.channel.send(request)
        value: object = worker.channel.recv()
        if not is_shard_outcome(value):
            raise ValueError("Invalid worker outcome")
        if (
            value["strategy_path"] != request["strategy_path"]
            or value["shard_path"] != request["shard_path"]
        ):
            raise ValueError("Worker returned a different assignment")
        outcome = value
        failure = None
    except Exception as exc:
        outcome = None
        failure = f"{type(exc).__name__}: {exc}"
    _publish(worker, assignment, outcome, failure, events)


def _publish(
    worker: Worker,
    assignment: int,
    outcome: BacktestShardReturn | None,
    failure: str | None,
    events: Queue[Receipt],
) -> None:
    with worker.receipt_lock:
        if worker.committed or worker.assignment != assignment:
            return
        receipt = Receipt(assignment, monotonic(), outcome, failure)
        worker.receipt = receipt
        events.put(receipt)


def _launch(worker: Worker) -> None:
    child = worker.child_channel
    if child is None:
        return
    try:
        worker.process.start()
    finally:
        child.close()
        worker.launch_complete.set()
        worker.child_channel = None


def _retire(worker: Worker) -> None:
    if worker.child_channel is not None:
        if worker.reader is None:
            worker.child_channel.close()
        elif not worker.launch_complete.wait(timeout=1.0):
            raise SupervisorError("Executor worker startup did not finish")
    if worker.process.pid is not None:
        if worker.process.is_alive():
            worker.process.kill()
        worker.process.join(timeout=1.0)
        if worker.process.is_alive():
            raise SupervisorError("Could not reap executor worker")
    worker.channel.close()
    if worker.reader is not None:
        worker.reader.join(timeout=1.0)
        if worker.reader.is_alive():
            raise SupervisorError("Could not stop worker channel reader")
    worker.process.close()


def _failure(worker: Worker, message: str) -> ShardFailure:
    request = worker.request
    if request is None:
        raise SupervisorError("Worker failure has no assignment")
    return {
        "strategy_path": request["strategy_path"],
        "shard_path": request["shard_path"],
        "status": "error",
        "error": {
            "kind": "worker_failure",
            "type": "ataraxia.errors.WorkerFailureError",
            "message": f"Shard {request['shard_path']}: {message}",
            "exit_code": worker.process.exitcode,
            "traceback": None,
        },
    }


def assignment_outcome(
    worker: Worker, receipt: Receipt | None, now: float, timeout: float
) -> BacktestShardReturn | None:
    """Return a single committed outcome, with expiry winning deadline races."""
    request = worker.request
    if request is None:
        return None
    if receipt is not None and receipt.completed < worker.started + timeout:
        if receipt.outcome is not None:
            return receipt.outcome
        return _failure(worker, receipt.failure or "Incomplete worker communication")
    if now >= worker.started + timeout:
        return {
            "strategy_path": request["strategy_path"],
            "shard_path": request["shard_path"],
            "status": "error",
            "error": {
                "kind": "timeout",
                "type": "ataraxia.errors.ShardTimeoutError",
                "message": (
                    f"Shard {request['shard_path']} exceeded its "
                    f"{timeout:g}-second deadline"
                ),
                "timeout_seconds": timeout,
                "elapsed_seconds": now - worker.started,
                "traceback": None,
            },
        }
    if worker.process.exitcode is not None:
        # The reader may still be validating a complete message from an exited child.
        if worker.reader is not None and worker.reader.is_alive():
            return None
        return _failure(worker, "Executor worker exited without an outcome")
    return None


def _dispatch(
    worker: Worker,
    request: ShardInput,
    assignment: int,
    events: Queue[Receipt],
    started: float,
) -> None:
    with worker.receipt_lock:
        worker.assignment = assignment
        worker.request = request
        worker.started = started
        worker.receipt = None
        worker.committed = False
    worker.reader = Thread(target=_exchange, args=(worker, events), daemon=True)
    worker.reader.start()


def _start(operation: ShardOperation) -> Worker:
    context = get_context("spawn")
    parent, child = context.Pipe()
    try:
        process = context.Process(target=_worker, args=(child, operation))
    except BaseException:
        parent.close()
        child.close()
        raise
    return Worker(process, parent, child_channel=child)


def _startup_failure(request: ShardInput, exc: Exception) -> ShardFailure:
    return {
        "strategy_path": request["strategy_path"],
        "shard_path": request["shard_path"],
        "status": "error",
        "error": {
            "kind": "worker_failure",
            "type": "ataraxia.errors.WorkerFailureError",
            "message": f"Worker startup failed for {request['shard_path']}: {exc}",
            "exit_code": None,
            "traceback": None,
        },
    }


def _fill_slots(
    workers: list[Worker],
    pending: Iterator[tuple[int, ShardInput]],
    size: int,
    operation: ShardOperation,
    events: Queue[Receipt],
    results: list[BacktestShardReturn],
) -> bool:
    for slot in range(size):
        if slot < len(workers) and workers[slot].request is not None:
            continue
        entry = next(pending, None)
        if entry is None:
            return True
        assignment, request = entry
        started = monotonic()
        if slot == len(workers):
            try:
                workers.append(_start(operation))
            except OSError as exc:
                results.append(_startup_failure(request, exc))
                return False
        _dispatch(workers[slot], request, assignment, events, started)
    return False


def _commit(
    workers: list[Worker],
    worker: Worker,
    receipt: Receipt | None,
    timeout: float,
    results: list[BacktestShardReturn],
) -> None:
    with worker.receipt_lock:
        if worker.committed:
            return
        receipt = worker.receipt or receipt
        outcome = assignment_outcome(worker, receipt, monotonic(), timeout)
        if outcome is None:
            return
        worker.committed = True
        reusable = (
            receipt is not None
            and receipt.outcome is not None
            and outcome is receipt.outcome
        )
        if reusable:
            worker.request = None
    results.append(outcome)
    # Killing and reaping must not delay publication from another assignment.
    if not reusable:
        _retire(worker)
        workers.remove(worker)


def _drain_receipts(
    workers: list[Worker],
    events: Queue[Receipt],
    timeout: float,
    results: list[BacktestShardReturn],
    receipt: Receipt | None = None,
) -> None:
    while True:
        if receipt is None:
            try:
                receipt = events.get_nowait()
            except Empty:
                return
        for worker in tuple(workers):
            if worker.request is not None and worker.assignment == receipt.assignment:
                _commit(workers, worker, receipt, timeout, results)
                break
        receipt = None


def _collect(
    workers: list[Worker],
    events: Queue[Receipt],
    timeout: float,
    results: list[BacktestShardReturn],
) -> None:
    try:
        receipt = events.get(timeout=0.01)
    except Empty:
        receipt = None
    _drain_receipts(workers, events, timeout, results, receipt)
    for worker in tuple(workers):
        # Cleanup may have admitted new receipts; preserve their arrival order.
        _drain_receipts(workers, events, timeout, results)
        _commit(workers, worker, None, timeout, results)


def _cleanup(workers: Sequence[Worker]) -> None:
    errors: list[Exception] = []
    for worker in workers:
        try:
            _retire(worker)
        except Exception as exc:
            errors.append(exc)
    if errors:
        raise SupervisorError("Executor worker cleanup failed") from errors[0]


def run_shards(
    requests: Sequence[ShardInput], size: int, timeout: float, operation: ShardOperation
) -> tuple[BacktestShardReturn, ...]:
    """Return outcomes in arrival order from independently supervised workers.

    Cleanup failures propagate as SupervisorError.

    Raises:
        ValueError: If pool size or timeout is invalid.
    """
    if size < 1 or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Pool size and timeout must be positive and finite")
    workers: list[Worker] = []
    events: Queue[Receipt] = Queue()
    results: list[BacktestShardReturn] = []
    pending = iter(enumerate(requests))
    exhausted = False
    try:
        while not exhausted or any(worker.request is not None for worker in workers):
            exhausted = _fill_slots(workers, pending, size, operation, events, results)
            _collect(workers, events, timeout, results)
        return tuple(results)
    finally:
        _cleanup(workers)
