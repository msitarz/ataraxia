# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz


import pytest

from ataraxia.source import SourceNode, SourceRunner


def test_source_runner():
    """Should return stored item."""

    sr = SourceRunner[int]()

    sr.item = 1

    assert sr() == 1


def test_source_node():
    """Should set runner's item from provider and raise StopIteration."""

    class TestProvider:
        def __init__(self):
            self.iterator = iter(range(3, 5))

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def __iter__(self):
            return self

        def __next__(self):
            return next(self.iterator)

    sn = SourceNode(TestProvider())

    iterator = iter(sn)
    value_1 = next(iterator)
    sn.send(value_1)

    assert sn.runner() == 3

    value_2 = next(iterator)
    sn.send(value_2)

    assert sn.runner() == 4

    with pytest.raises(StopIteration):
        next(iterator)


def test_source_node_delegates_provider_lifecycle():
    """Should enter and exit its provider unchanged."""

    class TestProvider:
        def __init__(self):
            self.entered = 0
            self.exit_args = None

        def __enter__(self):
            self.entered += 1
            return self

        def __exit__(self, *args):
            self.exit_args = args
            return False

        def __iter__(self):
            return self

        def __next__(self):
            raise StopIteration

    provider = TestProvider()
    source = SourceNode(provider)
    error = RuntimeError("compute failed")

    assert source.__enter__() is source
    assert source.__exit__(RuntimeError, error, None) is False
    assert provider.entered == 1
    assert provider.exit_args == (RuntimeError, error, None)
