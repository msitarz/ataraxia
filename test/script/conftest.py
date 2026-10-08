# SPDX-License-Identifier: Apache-2.0
"""Shared temporary arrangements for registry process tests."""

from test.script.registry_layout import literal_package as literal_package
from test.script.selection_inputs import (
    changed_selection,
    cli_cache_destination,
    cli_existing_destination,
    cli_missing_record,
    prepared_selection,
    unsupported_selection,
)
from test.script.selection_manifest import manifest_expected, selection_expected

__all__ = [
    "changed_selection",
    "cli_cache_destination",
    "cli_existing_destination",
    "cli_missing_record",
    "literal_package",
    "manifest_expected",
    "prepared_selection",
    "selection_expected",
    "unsupported_selection",
]
