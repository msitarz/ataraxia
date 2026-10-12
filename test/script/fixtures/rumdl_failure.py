#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""External formatter fixture that reports failure without formatting."""

import sys

sys.stderr.write("rumdl unavailable\n")
raise SystemExit(2)
