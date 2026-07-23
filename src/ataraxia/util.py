# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Various utilities."""

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, TypeIs

from ataraxia.compute import Sink
from ataraxia.errors import ModuleError


def import_file(path: str | Path) -> ModuleType:
    """Return module from path.

    Raises:
        ModuleError: When cannot load path.
    """
    path = Path(path).resolve()
    module_name = path.stem

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ModuleError("Cannot load module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_sink(obj: Any) -> TypeIs[Sink[..., Any]]:
    """Return True if obj is Sink, False otherwise."""
    return isinstance(obj, Sink)


def is_type(obj: Any) -> TypeIs[type]:
    """Return True if obj is type, False otherwise."""
    return isinstance(obj, type)
