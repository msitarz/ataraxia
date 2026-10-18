#!/usr/bin/env python3
"""Controlled GitHub CLI boundary for work-close integration tests."""

import json
import os
import subprocess
import sys


def main() -> None:
    command = sys.argv[1:]
    if command[:2] == ["pr", "view"]:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        if os.environ.get("GH_PR_MALFORMED") == "1":
            sys.stdout.write("{}\n")
            return
        sys.stdout.write(
            json.dumps({
                "number": int(os.environ.get("GH_PR_NUMBER", "17")),
                "state": os.environ.get("GH_PR_STATE", "OPEN"),
                "headRefName": os.environ.get("GH_HEAD_REF_NAME", branch),
                "headRefOid": os.environ.get("GH_HEAD_REF_OID", head),
            })
            + "\n"
        )
    elif command[:2] == ["repo", "view"]:
        sys.stdout.write(
            json.dumps({
                "nameWithOwner": os.environ.get(
                    "GH_REPOSITORY", "example/work-close-fixture"
                )
            })
            + "\n"
        )
    elif command[:1] == ["api"]:
        endpoint = command[1]
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        repository = os.environ.get("GH_HEAD_REPOSITORY", "example/work-close-fixture")
        if endpoint.endswith("/files?per_page=100"):
            sys.stdout.write(
                json.dumps([
                    {"filename": path}
                    for path in os.environ.get(
                        "GH_CHANGED_PATHS",
                        os.environ.get(
                            "GH_CHANGED_PATH", "doc/feat/parent/child/README.md"
                        ),
                    ).split(",")
                ])
                + "\n"
            )
        else:
            sys.stdout.write(
                json.dumps({
                    "head": {"sha": head, "repo": {"full_name": repository}},
                    "base": {"repo": {"full_name": "example/work-close-fixture"}},
                })
                + "\n"
            )
    else:
        raise SystemExit(f"unsupported gh invocation: {command}")


if __name__ == "__main__":
    main()
