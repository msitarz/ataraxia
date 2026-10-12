# SPDX-License-Identifier: Apache-2.0
"""Format an explicit commit body and commit the existing Git index."""

import os
import subprocess
import sys

if __package__:
    from script.check_commit_message import BODY_WIDTH, check_message
else:
    from check_commit_message import BODY_WIDTH, check_message


def format_body(body: str) -> str:
    """Format prose with isolated pinned rumdl settings.

    Returns:
        The formatted body.

    Raises:
        RuntimeError: If rumdl fails.
    """
    result = subprocess.run(
        [
            "rumdl",
            "fmt",
            "--stdin",
            "--stdin-filename",
            "commit-message.md",
            "--no-config",
            "--enable",
            "MD013",
            "--config",
            f"MD013.line-length = {BODY_WIDTH}",
            "--config",
            "MD013.reflow = true",
            "--config",
            "MD013.code-blocks = false",
            "--config",
            "MD013.code-spans = false",
            "--config",
            "MD013.headings = false",
            "--config",
            "MD013.tables = false",
        ],
        input=body,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    sys.stderr.write(result.stderr)
    if result.returncode:
        raise RuntimeError("rumdl failed to format the commit body")
    return result.stdout


def main() -> int:
    """Validate explicit inputs, then invoke ordinary Git commit.

    Returns:
        The Git commit exit status, or a validation failure status.
    """
    subject = os.environ.get("ATARAXIA_COMMIT_SUBJECT", "")
    body = os.environ.get("ATARAXIA_COMMIT_BODY", "")
    if not subject or "\n" in subject or "\r" in subject:
        sys.stderr.write("commit: SUBJECT must be a non-empty single line\n")
        return 2
    try:
        formatted = format_body(body) if body else ""
    except RuntimeError as error:
        sys.stderr.write(f"commit: {error}\n")
        return 1
    message = subject + ("\n\n" + formatted.rstrip("\n") if formatted else "")
    errors = check_message(message)
    if errors:
        for error in errors:
            sys.stderr.write(f"commit message format: {error}\n")
        return 1
    return subprocess.run(["git", "commit", "-m", message], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
