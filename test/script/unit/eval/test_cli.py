# SPDX-License-Identifier: Apache-2.0
"""Intent placeholders for generic evaluation harness CLI behavior."""

import pytest


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-1 CLI help for the native instruction setting",
)
def test_instructions_file_help_names_the_native_codex_setting() -> None:
    """Keep the optional flag distinct from generic context directories."""
    # Given
    # The CLI help is requested without starting repository preparation.

    # When
    # The user reads the -i / --instructions-file option description.

    # Then
    # It explains the staged path maps to -c model_instructions_file=PATH.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-1 ordered options and separator refusal",
)
def test_ordered_cli_options_preserve_positions_and_refuse_bad_boundaries() -> None:
    """Preserve option order while rejecting malformed separator placement."""
    # Given
    # Repeated directory and separator options, including default and bad cases.

    # When
    # The CLI parses the ordered option stream before preparation.

    # Then
    # Valid boundary assignments retain positions; invalid assignments refuse.
    pass
