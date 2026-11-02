# SPDX-License-Identifier: Apache-2.0
"""Ordered command-line options for the evaluation harness."""

import argparse
from collections.abc import Sequence
import difflib
from pathlib import Path
import re
from typing import NoReturn, override

from pydantic import ValidationError

from script.eval.model import (
    DirectoryOption,
    HarnessConfig,
    OrderedOption,
    SeparatorOption,
)

# Require one close option to avoid suggesting an ambiguous correction.
_OPTION_SUGGESTION_CUTOFF = 0.75

_NUMERIC_FIELDS = frozenset({
    "concurrency",
    "timeout_seconds",
    "cleanup_timeout_seconds",
    "grace_seconds",
    "output_limit_bytes",
    "progress_interval_seconds",
    "retry_limit",
    "quota_wait_limit_seconds",
    "quota_poll_interval_seconds",
    "quota_probe_budget",
    "capacity_retry_limit",
    "capacity_backoff_base_seconds",
    "capacity_backoff_cap_seconds",
})

_SEMANTIC_ERRORS = {
    "at least one directory is required": (
        "provide at least one -d/--directory parameter. "
        "Example: -d path/to/contexts -m gpt-6-luna -e low -n"
    ),
    "at least one model is required": "provide at least one -m/--model parameter.",
    "at least one effort is required": "provide at least one -e/--effort parameter.",
    "execution requires an output directory": (
        "execution requires -o/--output-directory; provide one or use -n/--dry-run."
    ),
    "grace_seconds must be less than cleanup_timeout_seconds": (
        "--grace-seconds must be less than --cleanup-timeout-seconds."
    ),
    "separators must occur singly between directories": (
        "place each -s/--separator between two -d/--directory parameters."
    ),
    "separator contains an unknown or dangling escape": (
        r"-s/--separator supports only \n, \r, \t, and \\ escapes."
    ),
    "capacity retries require backoff base and cap durations": (
        "--capacity-retry-limit requires --capacity-backoff-base-seconds "
        "and --capacity-backoff-cap-seconds."
    ),
    "capacity backoff cap must be at least its base": (
        "--capacity-backoff-cap-seconds must be at least "
        "--capacity-backoff-base-seconds."
    ),
}


class _ArgumentParser(argparse.ArgumentParser):
    """Render argument failures without repeating the full help text."""

    @override
    def error(self, message: str) -> NoReturn:
        """Exit with concise guidance for an invalid command line."""
        prefix = "unrecognized arguments: "
        if message.startswith(prefix):
            unknown = message.removeprefix(prefix).split()[0]
            options = [
                name for name in self._option_string_actions if name.startswith("--")
            ]
            matches = difflib.get_close_matches(
                unknown.split("=", 1)[0], options, n=2, cutoff=_OPTION_SUGGESTION_CUTOFF
            )
            message = f"unrecognized argument {unknown!r}."
            if len(matches) == 1:
                message += f" Did you mean {matches[0]}?"
        else:
            numeric = re.fullmatch(
                r"argument (.+?): invalid (int|float) value: .*", message
            )
            if numeric:
                kind = "integer" if numeric[2] == "int" else "number"
                message = f"{numeric[1]} requires a valid {kind}."
        self.exit(2, f"error: {message}\nRun with --help for all options.\n")


def _validation_message(error: ValidationError) -> str:
    """Translate the first model validation failure into public CLI guidance.

    Returns:
        A concise explanation using command-line option names.
    """
    detail = error.errors(include_url=False, include_input=False)[0]
    location = detail["loc"]
    if location and location[0] in _NUMERIC_FIELDS:
        option = "--" + str(location[0]).replace("_", "-")
        match detail["type"]:
            case "greater_than":
                return f"{option} must be greater than {detail['ctx']['gt']}."
            case "greater_than_equal":
                return f"{option} must be at least {detail['ctx']['ge']}."
            case "finite_number":
                return f"{option} must be finite."
        return f"invalid value for {option}; check --help for its expected value."
    cause = detail.get("ctx", {}).get("error")
    return _SEMANTIC_ERRORS.get(
        str(cause), "invalid option combination; check --help for supported options."
    )


class OrderedAction(argparse.Action):
    """Collect directory and separator events in their original order."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[str] | None,
        option_string: str | None = None,
    ) -> None:
        """Append one event, preserving intervening unrelated flags."""
        assert isinstance(values, str)
        options: list[OrderedOption] = getattr(namespace, self.dest, None) or []
        if option_string in ("-d", "--directory"):
            options.append(DirectoryOption(position=len(options), path=Path(values)))
        else:
            options.append(SeparatorOption(position=len(options), value=values))
        setattr(namespace, self.dest, options)


def parse_config(argv: Sequence[str], /) -> HarnessConfig:
    """Parse and validate options without accessing inputs or the provider.

    Returns:
        A validated configuration retaining ordered context boundaries.
    """
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        return HarnessConfig(
            ordered_options=tuple(args.ordered_options or ()),
            models=tuple(args.models or ()),
            efforts=tuple(args.efforts or ()),
            concurrency=args.concurrency,
            output_directory=args.output_directory,
            dry_run=args.dry_run,
            timeout_seconds=args.timeout_seconds,
            cleanup_timeout_seconds=args.cleanup_timeout_seconds,
            grace_seconds=args.grace_seconds,
            output_limit_bytes=args.output_limit_bytes,
            quiet=args.quiet,
            progress_interval_seconds=args.progress_interval_seconds,
            retry_limit=args.retry_limit,
            retry_nonzero_exit=args.retry_nonzero_exit,
            quota_wait_enabled=args.quota_wait_enabled,
            quota_wait_limit_seconds=args.quota_wait_limit_seconds,
            quota_poll_interval_seconds=args.quota_poll_interval_seconds,
            quota_probe_budget=args.quota_probe_budget,
            capacity_retry_limit=args.capacity_retry_limit,
            capacity_backoff_base_seconds=args.capacity_backoff_base_seconds,
            capacity_backoff_cap_seconds=args.capacity_backoff_cap_seconds,
            instructions_file_path=args.instructions_file_path,
        )
    except ValidationError as error:
        parser.error(_validation_message(error))


def _parser() -> argparse.ArgumentParser:
    """Describe the supported unattended settings and validated defaults.

    Returns:
        The argument parser used for one invocation.
    """
    parser = _ArgumentParser(
        description="Run a frozen evaluation matrix.",
        epilog=(
            "Exit codes: 0 success, 1 failure, 2 invalid arguments, "
            "3 evidence setup or recording incomplete, 130 cancellation. "
            "Progress is best effort and may be dropped if stderr is slow."
        ),
    )
    parser.add_argument(
        "-d",
        "--directory",
        dest="ordered_options",
        action=OrderedAction,
        help="context directory (repeat in order)",
    )
    parser.add_argument(
        "-s",
        "--separator",
        dest="ordered_options",
        action=OrderedAction,
        help="separator between adjacent directories",
    )
    parser.add_argument(
        "-m", "--model", dest="models", action="append", help="model (repeat in order)"
    )
    parser.add_argument(
        "-e",
        "--effort",
        dest="efforts",
        action="append",
        help="reasoning effort (repeat in order)",
    )
    parser.add_argument("-c", "--concurrency", type=int, default=1)
    parser.add_argument("-o", "--output-directory", type=Path)
    parser.add_argument("-n", "--dry-run", action="store_true")
    parser.add_argument(
        "-i",
        "--instructions-file",
        dest="instructions_file_path",
        type=Path,
        help=(
            "freeze and stage as -c model_instructions_file=PATH, replacing "
            "Codex default system instructions; directory files remain context"
        ),
    )
    parser.add_argument("--quiet", action="store_true", help="suppress progress")
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    parser.add_argument("--cleanup-timeout-seconds", type=float, default=10.0)
    parser.add_argument("--grace-seconds", type=float, default=0.0)
    parser.add_argument(
        "--output-limit-bytes",
        type=int,
        default=0,
        help="0 disables the output byte cap",
    )
    parser.add_argument("--progress-interval-seconds", type=float, default=1.0)
    parser.add_argument("--retry-limit", type=int, default=0)
    parser.add_argument("--retry-nonzero-exit", action="store_true")
    parser.add_argument(
        "--wait-for-quota",
        dest="quota_wait_enabled",
        action="store_true",
        help=("enable potentially billable supervised quota probes"),
    )
    parser.add_argument("--quota-wait-limit-seconds", type=float)
    parser.add_argument("--quota-poll-interval-seconds", type=float, default=60.0)
    parser.add_argument("--quota-probe-budget", type=int)
    parser.add_argument(
        "--capacity-retry-limit",
        type=int,
        default=0,
        help=("maximum retries for recognized transient model-capacity failures"),
    )
    parser.add_argument("--capacity-backoff-base-seconds", type=float)
    parser.add_argument("--capacity-backoff-cap-seconds", type=float)
    return parser
