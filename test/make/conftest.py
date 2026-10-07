# SPDX-License-Identifier: Apache-2.0
"""Reuse registry arrangements needed by Make target tests."""

from test.script.registry_transport import (
    registry_literal_case,
    registry_missing_case,
    registry_project,
)

__all__ = ["registry_literal_case", "registry_missing_case", "registry_project"]
