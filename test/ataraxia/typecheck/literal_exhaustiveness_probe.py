# SPDX-License-Identifier: Apache-2.0
from typing import Literal

type Change = Literal["declaration", "evidence", "file", "link", "record"]


def closed_match(value: Change) -> None:
    match value:
        case "declaration" | "evidence" | "file" | "link":
            return


def open_match(value: str) -> None:
    match value:
        case "declaration" | "evidence" | "file" | "link" | "record":
            return
