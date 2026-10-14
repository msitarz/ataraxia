# SPDX-License-Identifier: Apache-2.0
from typing import Literal, TypeIs, assert_type, get_args

type ProbeName = Literal["first", "second"]


def is_probe_name(value: str) -> TypeIs[ProbeName]:
    return value in get_args(ProbeName.__value__)


def consume_probe_name(value: ProbeName) -> None:
    pass


def callers(external: str) -> None:
    if is_probe_name(external):
        assert_type(external, ProbeName)
        consume_probe_name(external)
    consume_probe_name(external)  # E: is not assignable
