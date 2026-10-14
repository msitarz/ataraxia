# SPDX-License-Identifier: Apache-2.0
"""Replace a reviewed workspace file with a FIFO at its descriptor open."""

import os
from pathlib import Path
import sys


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from script import sandbox, sandbox_disposition

    source, root, generation = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    original_open = os.open
    replaced = False

    def replacing_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal replaced
        if path == "tracked.txt" and dir_fd is not None and not replaced:
            os.unlink(path, dir_fd=dir_fd)
            os.mkfifo(path, 0o600, dir_fd=dir_fd)
            replaced = True
        return original_open(path, flags, mode, dir_fd=dir_fd)

    os.open = replacing_open
    try:
        with sandbox.locked_sandbox(root, "execute", generation) as scope:
            sandbox_disposition.record_disposition(
                scope,
                owner_id="orchestrator-fixture",
                source_repository=source,
                work="doc/feat/example/README.md",
                reviewed=sandbox_disposition.ReviewedDisposition(
                    "maintainer-fixture",
                    "review-fifo-race",
                    sandbox_disposition.MaterialDecision("discard", "review-workspace"),
                    sandbox_disposition.MaterialDecision(
                        "discard", "review-no-outputs"
                    ),
                ),
            )
    except ValueError as error:
        if replaced and "replaced" in str(error):
            sys.stdout.write("refused replaced non-regular workspace entry\n")
            return
        raise
    finally:
        os.open = original_open
    raise AssertionError("disposition accepted a file replaced by a FIFO")


if __name__ == "__main__":
    main()
