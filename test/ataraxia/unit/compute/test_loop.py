# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
from dataclasses import dataclass, field
from operator import itemgetter
from typing import TYPE_CHECKING

import pytest

from ataraxia.compute import Runner, Source
from ataraxia.compute.loop import (
    compute,
    compute_step,
    prime_catalog,
)

if TYPE_CHECKING:
    from ataraxia.bar import Bar


@pytest.fixture
def single_dep():
    # Runners are also frozen dataclasses for easy assert

    @dataclass(frozen=True)
    class BRunner:
        def __call__(self):
            return 1

    @dataclass(frozen=True)
    class B:
        def deps(self):
            return {}

        def factory(self):
            return BRunner()

    @dataclass(frozen=True)
    class ARunner:
        def __call__(self, b: int):
            return b + 3

    @dataclass(frozen=True)
    class A:
        def deps(self):
            return {"b": B()}

        def factory(self):
            return ARunner()

    return {"BRunner": BRunner, "B": B, "ARunner": ARunner, "A": A}


@pytest.fixture
def source_sink():
    class SrcRunner:
        def __call__(self):
            return self.next_item

    @dataclass(frozen=True)
    class Src:
        runner: Runner = field(default_factory=SrcRunner)
        exit_args: list[tuple[object, object, object]] = field(
            default_factory=list, compare=False, hash=False
        )

        def deps(self):
            return {}

        def factory(self):
            return self.runner

        def send(self, item):
            self.runner.next_item = item

        def __iter__(self):
            return (x for x in (1, 3))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.exit_args.append((exc_type, exc_value, traceback))
            return False

    @dataclass(frozen=True)
    class SnkRunner:
        def __call__(self, item: int):
            return item + 7

    @dataclass(frozen=True)
    class Snk:
        source: Source = field(default_factory=Src)

        def deps(self):
            return {"item": self.source}

        def factory(self):
            return SnkRunner()

        def sources(self):
            return (self.source,)

        def consumer(self):
            return None

    return {"Src": Src, "Snk": Snk}


def test_compute_closes_source_on_exhaustion(source_sink):
    Snk = itemgetter("Snk")(source_sink)
    snk = Snk()

    assert list(compute(snk)) == [
        {snk.source: 1, snk: 8},
        {snk.source: 3, snk: 10},
    ]
    assert snk.source.exit_args == [(None, None, None)]


def test_compute_closes_source_when_runner_raises(source_sink):
    Src = itemgetter("Src")(source_sink)

    @dataclass(frozen=True)
    class FailingRunner:
        def __call__(self, item: int):
            raise RuntimeError("sink runner failed")

    @dataclass(frozen=True)
    class FailingSink:
        source: Source

        def deps(self):
            return {"item": self.source}

        def factory(self):
            return FailingRunner()

        def sources(self):
            return (self.source,)

        def consumer(self):
            return None

    source = Src()

    with pytest.raises(RuntimeError, match="sink runner failed"):
        next(compute(FailingSink(source)))

    ((exc_type, exc_value, traceback),) = source.exit_args
    assert exc_type is RuntimeError
    assert str(exc_value) == "sink runner failed"
    assert traceback is not None


def test_compute_closes_source_when_generator_is_closed(source_sink):
    Snk = itemgetter("Snk")(source_sink)
    snk = Snk()
    computed = compute(snk)

    next(computed)
    computed.close()

    ((exc_type, exc_value, traceback),) = snk.source.exit_args
    assert exc_type is GeneratorExit
    assert isinstance(exc_value, GeneratorExit)
    assert traceback is not None


@pytest.mark.parametrize(
    ("runner", "names"),
    [
        (lambda item: item, ("itme",)),
        (lambda item: item, ()),
        (lambda item: item, ("item", "extra")),
        (lambda item, /: item, ("item",)),
    ],
)
def test_invalid_dependency_names_fail_preparation(single_dep, runner, names):
    from ataraxia.errors import DependencyError

    class Invalid:
        def deps(self):
            return dict.fromkeys(names, single_dep["B"]())

        def factory(self):
            return runner

    with pytest.raises(DependencyError, match="Invalid dependencies") as error:
        prime_catalog((Invalid(),))
    assert isinstance(error.value.__cause__, TypeError)


@pytest.mark.parametrize(
    ("runner", "names"),
    [
        (lambda *, item: item, ("item",)),
        (lambda item=1: item, ()),
        (lambda **kwargs: kwargs, ("arbitrary",)),
        (lambda *args: args, ()),
    ],
)
def test_valid_dependency_signatures(single_dep, runner, names):
    class Valid:
        def deps(self):
            return dict.fromkeys(names, single_dep["B"]())

        def factory(self):
            return runner

    node = Valid()
    assert prime_catalog((node,))[node] is runner


def test_wiring_failure_precedes_source_entry(source_sink):
    from ataraxia.errors import DependencyError

    class InvalidSink(source_sink["Snk"]):
        def deps(self):
            return {"itme": self.source}

    sink = InvalidSink()
    with pytest.raises(DependencyError):
        next(compute(sink))
    assert sink.source.exit_args == []


def test_uninspectable_runner_fails_preparation():
    from ataraxia.errors import DependencyError

    class Node:
        def deps(self):
            return {}

        def factory(self):
            return int

    with pytest.raises(DependencyError) as error:
        prime_catalog((Node(),))
    assert isinstance(error.value.__cause__, ValueError)


def test_preparation_does_not_evaluate_type_only_annotations():
    class AnnotatedRunner:
        def __call__(self, item: Bar | None = None) -> int:
            return 7

    class Node:
        def deps(self):
            return {}

        def factory(self):
            return AnnotatedRunner()

    node = Node()
    catalog = prime_catalog((node,))
    assert compute_step((node,), catalog)[node] == 7
