# SPDX-License-Identifier: Apache-2.0
"""Git clean/smudge filter that normalizes committed line endings."""

import sys


def main() -> None:
    """Convert CRLF worktree bytes to LF blobs and back."""
    content = sys.stdin.buffer.read()
    if sys.argv[1] == "clean":
        content = content.replace(b"\r\n", b"\n")
    else:
        content = content.replace(b"\n", b"\r\n")
    sys.stdout.buffer.write(content)


if __name__ == "__main__":
    main()
