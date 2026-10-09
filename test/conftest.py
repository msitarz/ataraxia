# SPDX-License-Identifier: Apache-2.0
"""Load bounded Hypothesis settings for repository tests."""

import os

from hypothesis import settings

defaults = settings.get_profile("default")
settings.register_profile("local", defaults, max_examples=100)
settings.register_profile("ci", defaults, max_examples=100, derandomize=True)
settings.load_profile("ci" if "CI" in os.environ else "local")
