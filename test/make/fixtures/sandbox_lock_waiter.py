# SPDX-License-Identifier: Apache-2.0
"""Wait for the shared sandbox lock and report when it becomes available."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def main() -> None:
    """Block on the lock and expose deterministic process barriers."""
    from script.sandbox import locked_sandbox

    root = Path(sys.argv[1])
    name = sys.argv[2]
    generation = sys.argv[3]
    sys.stdout.write("waiting\n")
    sys.stdout.flush()
    with locked_sandbox(root, name, generation):
        sys.stdout.write("acquired\n")
        sys.stdout.flush()
        sys.stdin.buffer.read(1)


if __name__ == "__main__":
    main()
