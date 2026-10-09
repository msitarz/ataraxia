# SPDX-License-Identifier: Apache-2.0
"""Typed integer and CSV-backed source arrangements for compute tests."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Self

from ataraxia.bar import Bar
from ataraxia.compute.protocol import Computable, Sink, Source
from ataraxia.provider import BarProvider
from ataraxia.source import SourceNode

type ContextExit = tuple[
    type[BaseException] | None,
    BaseException | None,
    TracebackType | None,
]


@dataclass
class IntegerSourceContext:
    """Record source context state and its precise exit arguments."""

    is_open: bool = False
    is_closed: bool = False
    exit_args: ContextExit | None = None


class IntegerSourceRunner:
    """Return the latest integer sent by the compute loop."""

    def __init__(self) -> None:
        self.item = 0

    def __call__(self) -> int:
        return self.item


@dataclass(frozen=True)
class IntegerSource(Source[int, [], int]):
    """Yield 1 and 3 while retaining its runner and observable context state."""

    items: tuple[int, ...] = (1, 3)
    runner: IntegerSourceRunner = field(default_factory=IntegerSourceRunner)
    context: IntegerSourceContext = field(
        default_factory=IntegerSourceContext, compare=False, hash=False
    )

    def deps(self) -> Mapping[str, Computable[..., int]]:
        return {}

    def factory(self) -> IntegerSourceRunner:
        return self.runner

    def send(self, item: int) -> None:
        self.runner.item = item

    def __iter__(self) -> Iterator[int]:
        return iter(self.items)

    def __enter__(self) -> Self:
        self.context.is_open = True
        self.context.is_closed = False
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        self.context.exit_args = (exc_type, exc_value, traceback)
        self.context.is_open = False
        self.context.is_closed = True
        return False


@dataclass(frozen=True)
class IntegerSinkRunner:
    """Add seven to each integer received from the source."""

    def __call__(self, item: int) -> int:
        return item + 7


@dataclass(frozen=True)
class IntegerSink(Sink[[int], int]):
    """Consume values from one injected integer source."""

    source: IntegerSource

    def deps(self) -> Mapping[str, IntegerSource]:
        return {"item": self.source}

    def factory(self) -> IntegerSinkRunner:
        return IntegerSinkRunner()

    def sources(self) -> tuple[IntegerSource, ...]:
        return (self.source,)

    def consumer(self) -> None:
        return None


def integer_source_sink() -> tuple[IntegerSink, IntegerSource]:
    """Return a sink and the same injected source that yields 1 and 3."""
    source = IntegerSource()
    return IntegerSink(source), source


def two_bar_csv_source(path: Path) -> tuple[SourceNode[Bar], BarProvider]:
    """Write two literal bars and return their real source and provider."""
    path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "1,100,102,99,101,10\n"
        "2,104,108,103,106,20\n",
        encoding="utf-8",
    )
    provider = BarProvider(path)
    return SourceNode[Bar](provider), provider
