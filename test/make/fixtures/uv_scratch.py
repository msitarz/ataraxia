#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Model process-owned home and scratch writes during a Make tool invocation."""

import os
from pathlib import Path


def main() -> None:
    """Write cache witnesses without touching the requested repository files."""
    (Path(os.environ["HOME"]) / "cache").write_text("process home cache\n")
    (Path(os.environ["TMPDIR"]) / "fixture-scratch-witness").write_bytes(
        b"process scratch cache\n"
    )


if __name__ == "__main__":
    main()
