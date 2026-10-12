# SPDX-License-Identifier: Apache-2.0
"""Render Mermaid source from standard input to validate it."""

import sys
from typing import Literal

import mermaidx


def main() -> Literal[0, 1]:
    """Validate stdin by forcing QuickJS SVG rendering without saving it.

    Returns:
        0 when rendering succeeds; 1 when the backend rejects the source.
    """
    source = sys.stdin.read()
    try:
        mermaidx.render(source, backend="quickjs").svg()
    except Exception as error:
        sys.stderr.write(f"{error}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
