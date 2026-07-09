# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Computation module.

An elastic computation model with dependency injection.
"""

from collections.abc import Hashable
import dataclasses
from dataclasses import is_dataclass
from typing import (
    Any,
    ClassVar,
    NamedTuple,
    Protocol,
    _ProtocolMeta,
    override,
    runtime_checkable,
)


def _is_dataclass_frozen(cls: type) -> bool:
    """Check if cls is a frozen dataclass.

    Args:
        cls: a class to check.

    Returns:
        bool: True if cls is a frozen dataclass, False otherwise.
    """
    if is_dataclass(cls) and hasattr(dataclasses, "_PARAMS"):
        params = getattr(cls, dataclasses._PARAMS, None)

        return getattr(params, "frozen", False)

    return False


class _ComputeMeta(_ProtocolMeta):
    """Base metaclass for computation classes.

    Use this metaclass to ensure that runtime check of each computation node is
    hashable using its attributes rather than identity.  Currently it requires a
    frozen dataclass as hashable implementation.
    """

    @override
    def __instancecheck__(cls, instance: object):
        if not super().__instancecheck__(instance):
            return False

        if _is_dataclass_frozen(type(instance)):
            return True

        raise TypeError("Instance and class must be a frozen dataclass")


class ComputableNode[**P, R](Protocol, metaclass=_ComputeMeta):
    """Computable node protocol.

    Computable node acts as a coroutine similar to a generator.  Attributes can keep
    state between invocations.
    """

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """ComputableNode implementation.

        Parameters will be provided via dependency injection defined in ComputableSpec.

        Return value will be fed into ComputableNode(s) depending on it.
        """
        ...


@runtime_checkable
class ComputableSpec[**P, R](Hashable, Protocol, metaclass=_ComputeMeta):
    """Computable specification protocol.

    Defines computation specification to be executed in a computation loop
    providing dependencies and initial parameters.

    Attributes:
        init_params: initial params for ComputableNode.  It must be a NamedTuple.  It
            will be unpacked as parameters to compute_node __init__ method.
        compute_node: class implementing ComputableNode protocol.
    """

    init_params: NamedTuple | None
    compute_node: ClassVar[type[ComputableNode[..., Any]]]

    def dependencies(
        self,
    ) -> tuple[type | ComputableSpec[..., Any], ...]:
        """Dependencies injected into ComputableNode on every invocation.

        Returns:
            Tuple of objects adhering to ComputableSpec protocol.
        """
        return ()

    def factory(self) -> ComputableNode[P, R]:
        """Instantiate compute_unit with init_params.

        Returns:
            Instance of compute_unit.
        """
        if hasattr(self, "init_params") and self.init_params:
            return self.compute_node(*self.init_params)
        else:
            return self.compute_node()
