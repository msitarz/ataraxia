# SPDX-License-Identifier: Apache-2.0
"""Construct and render a read-only plan for selected Work contracts.

API:
``make_plan`` validates explicit selections and returns a ``ClosePlan`` with
each Work's proposed criterion and outcome values, canonical parent or
dependency reference updates, and observed repository and pull request
metadata. ``render_plan`` turns that record into stable, newline-terminated
review text. ``ClosePlanningError`` reports when selections, contract
structure, references, or metadata do not support a safe plan.

Implementation:
Planning reads selected contracts through the shared Work source and structure
modules, then derives criterion outcomes and readiness. Readiness depends on
whether any proposed criterion remains TODO; a Work outcome of ABORT may
coexist with unresolved TODO criteria. Reference planning scans tracked
Markdown and permits updates only for supported canonical map rows. Git and
pull request queries provide the repository and head observations included in
the plan. This module prepares and presents a plan without applying it.
"""

from collections.abc import Sequence
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import override
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
from markdown_it.token import Token

from script.markdown.model import MarkdownParser
from script.work.contract import WorkCriterion, inspect_work, parse_criterion_status
from script.work.source import WorkSource, WorkSourceError, discover_work_sources
from script.work.work_close.model import (
    ClosePlan,
    CriterionPlan,
    ReferencePlan,
    WorkPlan,
    WorkResult,
)

_ABORT_REASON = "Maintainer confirmed abort during authorized closure."


class ClosePlanningError(ValueError):
    """Raised when a safe read-only closure plan cannot be established."""


def make_plan(
    selections: Sequence[str], abort_remaining: bool, markdown: MarkdownParser
) -> ClosePlan:
    """Validate explicit Work selections and capture a read-only closure plan.

    Returns:
        The validated closure plan.
    """
    root = _repository_root()
    contracts = _selected_contracts(root, selections)
    works = tuple(
        _work_plan(root, contract.path, contract.text, markdown, abort_remaining)
        for contract in contracts
    )
    pending = any(
        criterion.result == "TODO" for work in works for criterion in work.criteria
    )
    references = _references(root, contracts, works)
    repository, pr_number, branch, local_tip, remote_tip, head_repo, pr_head = _pr_head(
        root, tuple(work.path for work in works)
    )
    return ClosePlan(
        not pending,
        repository,
        pr_number,
        branch,
        local_tip,
        remote_tip,
        head_repo,
        pr_head,
        works,
        references,
    )


def render_plan(plan: ClosePlan) -> str:
    """Render stable, reviewable plan text.

    Returns:
        A newline-terminated plan.
    """
    lines = [
        "Closure plan: READY" if plan.ready else "Closure plan: PENDING DECISION",
        f"PR: #{plan.pr_number}",
        f"Repository: {plan.repository}",
        f"Branch: {plan.branch}",
        f"Local tip: {plan.local_tip}",
        f"Remote tip: {plan.remote_tip}",
        f"PR head repository: {plan.pr_head_repository}",
        f"PR head: {plan.pr_head}",
        "Works:",
    ]
    for work in plan.works:
        reason = f" (reason: {work.reason})" if work.reason else ""
        lines.append(f"  {work.result} {work.path}: {work.title}{reason}")
        for criterion in work.criteria:
            reason = (
                f" — {_ABORT_REASON}"
                if criterion.result == "ABORT" and criterion.status == "TODO"
                else ""
            )
            lines.append(
                f"    {criterion.identifier}: {criterion.status} -> "
                f"{criterion.result}{reason}"
            )
    lines.append("Reference updates:")
    for reference in plan.references:
        lines.extend((
            f"  {reference.path}",
            f"    - {reference.before}",
            f"    + {reference.after}",
        ))
    if not plan.ready:
        lines.append(
            "Decision required: ask the maintainer whether to abort the remaining "
            "TODO criteria. After explicit confirmation, rerun this selection "
            "with ABORT_REMAINING=true."
        )
    return "\n".join(lines) + "\n"


def _repository_root() -> Path:
    """Return the current repository root when invoked from that directory.

    Raises:
        ClosePlanningError: The current directory is not the repository root.
    """
    result = _run_git(["rev-parse", "--show-toplevel"])
    root = Path(result).resolve(strict=True)
    if Path.cwd().resolve() != root:
        raise ClosePlanningError("run work-close from the repository root")
    return root


def _selected_contracts(
    root: Path, selections: Sequence[str]
) -> tuple[WorkSource, ...]:
    """Resolve explicit selections and require every included Work README.

    Args:
        root: Repository root used to resolve selected paths.
        selections: Explicit Work README paths, relative or absolute within root.

    Returns:
        The discovered selected Work contracts.

    Raises:
        ClosePlanningError: A selection is missing, invalid, or unsafe.
    """
    if not selections or any(
        PurePosixPath(selection).name != "README.md" for selection in selections
    ):
        raise ClosePlanningError("select each Work README.md explicitly")
    try:
        contracts = discover_work_sources(root, selections)
    except WorkSourceError as exc:
        raise ClosePlanningError(str(exc)) from exc
    selected = {Path(selection).resolve(strict=True) for selection in selections}
    if selected != {contract.path for contract in contracts}:
        raise ClosePlanningError("selection must name every included Work README.md")
    return contracts


def _work_plan(
    root: Path, path: Path, source: str, markdown: MarkdownParser, abort_remaining: bool
) -> WorkPlan:
    """Inspect one Work contract and derive its proposed closure result.

    Args:
        root: Repository root used to record a relative contract path.
        path: Resolved path of the selected contract.
        source: Contract Markdown text.
        markdown: Parser used to inspect the contract.
        abort_remaining: Whether TODO criteria are proposed as ABORT.

    Returns:
        The selected Work's proposed plan.

    Raises:
        ClosePlanningError: The contract contains a validation diagnostic.
    """
    blocks = markdown.parse(source)
    inspection = inspect_work(blocks)
    if inspection.diagnostics:
        first = inspection.diagnostics[0]
        raise ClosePlanningError(f"{path}:{first.line}: {first.rule}: {first.context}")
    title = inspection.title
    assert title is not None
    criteria = _criteria_plan(inspection.criteria, abort_remaining)
    result = _work_result(criteria)
    reason = _work_reason(criteria, result)
    return WorkPlan(
        path.relative_to(root).as_posix(), title, result, tuple(criteria), reason
    )


def _criteria_plan(
    checked: tuple[WorkCriterion, ...], abort_remaining: bool
) -> list[CriterionPlan]:
    """Map checked criteria to their proposed statuses.

    Args:
        checked: Validated current criteria from the Work contract.
        abort_remaining: Whether TODO criteria are proposed as ABORT.

    Returns:
        Criterion plans preserving each current status and proposed result.
    """
    criteria: list[CriterionPlan] = []
    for criterion in checked:
        status = criterion.status
        result = "ABORT" if status == "ABORT" else status
        if status == "TODO" and abort_remaining:
            result = "ABORT"
        criteria.append(CriterionPlan(criterion.identifier, status, result))
    return criteria


def _work_result(criteria: list[CriterionPlan]) -> WorkResult:
    """Summarize proposed criterion results as one Work result.

    Args:
        criteria: Proposed results for the Work's criteria.

    Returns:
        ABORT if any criterion aborts, otherwise PENDING for TODO, else DONE.

        ABORT may coexist with unresolved TODO criteria; plan readiness is
        decided separately.
    """
    if any(item.result == "ABORT" for item in criteria):
        return "ABORT"
    if any(item.result == "TODO" for item in criteria):
        return "PENDING"
    return "DONE"


def _work_reason(criteria: list[CriterionPlan], result: WorkResult) -> str | None:
    """Explain an aborted Work result, if one was proposed.

    Args:
        criteria: Proposed results and current statuses for the Work.
        result: Summary result produced for the Work.

    Returns:
        The abort rationale, or None when the Work is not aborted.
    """
    if result != "ABORT":
        return None
    if any(item.status == "TODO" and item.result == "ABORT" for item in criteria):
        return _ABORT_REASON
    aborted = ", ".join(item.identifier for item in criteria if item.result == "ABORT")
    return f"already-aborted criteria: {aborted}"


def _references(
    root: Path,
    selected: tuple[WorkSource, ...],
    works: tuple[WorkPlan, ...],
) -> tuple[ReferencePlan, ...]:
    """Plan canonical parent and dependency map updates for selected Works.

    Args:
        root: Repository root containing tracked Markdown documents.
        selected: Selected Work contract sources.
        works: Proposed Work plans carrying repository-relative contract paths.

    Returns:
        Sorted exact source-span updates for references to selected Works.
    """
    selected_paths = {contract.path for contract in selected}
    works_by_path: dict[Path, WorkPlan] = {
        (root / work.path).resolve(): work for work in works
    }
    result: list[ReferencePlan] = []
    for contract in _markdown_documents(root):
        result.extend(
            _contract_references(
                root,
                contract,
                selected_paths,
                works_by_path,
                _is_work_contract(root, contract.path),
            )
        )
    return tuple(sorted(result, key=lambda item: (item.path, item.before)))


def _markdown_documents(root: Path) -> tuple[WorkSource, ...]:
    """Read tracked Markdown documents after checking their resolved paths.

    Args:
        root: Repository root used to enumerate and contain tracked files.

    Returns:
        Tracked Markdown sources with resolved paths and UTF-8 text.

    Raises:
        ClosePlanningError: A file is unsafe or cannot be read as UTF-8.
    """
    documents = []
    for relative in _run_git(["ls-files", "-z", "--", "*.md"]).split("\0"):
        if not relative:
            continue
        path = root / relative
        try:
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise ClosePlanningError(
                f"cannot inspect Markdown reference file {relative}: {exc}"
            ) from exc
        if path.is_symlink() or not resolved.is_relative_to(root):
            raise ClosePlanningError(f"unsafe Markdown reference file: {relative}")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ClosePlanningError(
                f"cannot inspect Markdown reference file {relative}: {exc}"
            ) from exc
        documents.append(WorkSource(resolved, text))
    return tuple(documents)


def _is_work_contract(root: Path, path: Path) -> bool:
    """Return whether a README is beneath root's Work contract tree in doc/feat."""
    return path.name == "README.md" and path.is_relative_to(root / "doc" / "feat")


def _contract_references(
    root: Path,
    contract: WorkSource,
    selected_paths: set[Path],
    works_by_path: dict[Path, WorkPlan],
    is_work_contract: bool,
) -> list[ReferencePlan]:
    """Collect rewritable references to selected Works from one document.

    Args:
        root: Repository root for resolving links.
        contract: Markdown document to inspect.
        selected_paths: Resolved paths of selected Work contracts.
        works_by_path: Proposed plans indexed by resolved contract path.
        is_work_contract: Whether the document uses the Work map contract.

    Returns:
        Proposed updates for canonical Children or Dependencies map entries.

    Raises:
        ClosePlanningError: A selected reference is ambiguous or overlaps.
    """
    tokens = MarkdownIt("commonmark").parse(contract.text)
    list_items = _list_items(tokens)
    lines = contract.text.splitlines()
    result = []
    for start, end, heading, children in list_items:
        targets = _selected_link_targets(
            children, root, contract.path.parent, selected_paths
        )
        # Also examine links outside list entries below. A selected link which
        # cannot be rewritten as one canonical map row is a hard refusal.
        for target, has_fragment in targets:
            if not is_work_contract or heading not in {"Children", "Dependencies"}:
                raise ClosePlanningError(
                    f"ambiguous reference to selected Work in {contract.path}: "
                    f"{lines[start].strip()}"
                )
            text = "\n".join(lines[start:end])
            result.append(
                _reference_plan(
                    root,
                    contract,
                    text,
                    start,
                    end,
                    target,
                    works_by_path,
                    has_fragment,
                    targets,
                )
            )
    _ensure_nonoverlapping_references(contract, result)
    _reject_unlisted_references(tokens, root, contract, selected_paths, list_items)
    return result


def _ensure_nonoverlapping_references(
    contract: WorkSource, references: list[ReferencePlan]
) -> None:
    """Reject reference source spans that overlap within a Markdown document.

    Args:
        contract: Source document containing the candidate spans.
        references: Proposed updates with one-based, inclusive line bounds.

    Raises:
        ClosePlanningError: Two candidate source spans overlap.
    """
    ordered = sorted(references, key=lambda item: item.line_start)
    furthest_end = 0
    for reference in ordered:
        if reference.line_start <= furthest_end:
            raise ClosePlanningError(
                f"overlapping Work map entries in {contract.path}: "
                f"line {reference.line_start} overlaps an earlier source span"
            )
        furthest_end = max(furthest_end, reference.line_end)


def _list_items(tokens: list[Token]) -> list[tuple[int, int, str, list[Token]]]:
    """Collect source spans and inline tokens for list items.

    Args:
        tokens: Parsed Markdown tokens for one source document.

    Returns:
        Zero-based, end-exclusive line spans paired with the active H2 section
        and the item's inline tokens.
    """
    section = ""
    result: list[tuple[int, int, str, list[Token]]] = []
    active: list[tuple[int, int, str, list[Token]]] = []
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.level == 0:
            section = ""
        elif token.type == "inline" and token.level == 1 and token.map:
            section = _heading_section(tokens, index, token.content, section)
        elif token.type == "list_item_open" and token.map:
            active.append((token.map[0], token.map[1], section, []))
        elif token.type == "inline" and token.children and active:
            active[-1][3].extend(token.children)
        elif token.type == "list_item_close" and active:
            result.append(active.pop())
    return result


def _heading_section(
    tokens: list[Token], index: int, content: str, current: str
) -> str:
    """Update the active section for an H2 heading token, if applicable.

    Returns:
        The heading content for an H2, or the unchanged current section.
    """
    if (
        index
        and tokens[index - 1].type == "heading_open"
        and tokens[index - 1].tag == "h2"
    ):
        return content
    return current


def _selected_link_targets(
    tokens: list[Token], root: Path, parent: Path, selected: set[Path]
) -> list[tuple[Path, bool]]:
    """Find links resolving to selected README paths and note fragments.

    Args:
        tokens: Markdown tokens to inspect, including inline HTML.
        root: Repository root for root-relative links.
        parent: Containing document directory for relative links.
        selected: Resolved selected Work README paths.

    Returns:
        Matched target paths paired with whether the link has a fragment.
    """
    targets = []
    for token in tokens:
        raw_links = []
        if token.type == "link_open":
            raw_links.append(token.attrGet("href"))
        elif token.type in {"html_inline", "html_block"}:
            raw_links.extend(_html_hrefs(token.content))
        for raw in raw_links:
            if not isinstance(raw, str):
                continue
            target, fragment = _local_link_target(raw, root, parent)
            if target in selected:
                targets.append((target, fragment))
    return targets


def _local_link_target(raw: str, root: Path, parent: Path) -> tuple[Path | None, bool]:
    """Resolve a local README link, returning its target and fragment flag.

    Args:
        raw: Link destination as written in Markdown.
        root: Repository root for root-relative links.
        parent: Containing document directory for relative links.

    Returns:
        A local README target paired with its fragment flag, or (None, False)
        for ignored non-README and external destinations.
    """
    parts = urlsplit(raw.strip("<>"))
    decoded = unquote(parts.path)
    if parts.scheme or parts.netloc or not decoded.endswith("README.md"):
        return None, False
    base = root if decoded.startswith("/") else parent
    relative = decoded.lstrip("/") if decoded.startswith("/") else decoded
    return (base / relative).resolve(), bool(parts.fragment)


def _html_hrefs(source: str) -> list[str]:
    """Extract href values from HTML tags in a Markdown token's source.

    Returns:
        Values of nonempty href attributes found in the source.
    """

    class LinkParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.hrefs: list[str] = []

        @override
        def handle_starttag(
            self, tag: str, attrs: list[tuple[str, str | None]]
        ) -> None:
            self.hrefs.extend(
                value for name, value in attrs if name == "href" and value
            )

    parser = LinkParser()
    parser.feed(source)
    return parser.hrefs


def _reject_unlisted_references(
    tokens: list[Token],
    root: Path,
    contract: WorkSource,
    selected: set[Path],
    list_items: list[tuple[int, int, str, list[Token]]],
) -> None:
    """Refuse selected Work links outside supported map-entry source spans.

    Args:
        tokens: Parsed tokens from the containing Markdown document.
        root: Repository root for resolving links.
        contract: Source document being checked.
        selected: Resolved selected Work README paths.
        list_items: Source spans recognized as Markdown list items.

    Raises:
        ClosePlanningError: A selected Work is referenced outside a map row.
    """
    for token in tokens:
        if token.type == "html_block" and _selected_link_targets(
            [token], root, contract.path.parent, selected
        ):
            raise ClosePlanningError(
                f"ambiguous reference to selected Work in {contract.path}: "
                f"{token.content.strip()}"
            )
        if token.type != "inline" or not token.children:
            continue
        targets = _selected_link_targets(
            token.children, root, contract.path.parent, selected
        )
        if targets and token.level == 1 and not token.map:
            raise ClosePlanningError(
                f"ambiguous reference to selected Work in {contract.path}: "
                f"{token.content}"
            )
        if (
            targets
            and token.map
            and not any(start <= token.map[0] < end for start, end, *_ in list_items)
        ):
            raise ClosePlanningError(
                f"ambiguous reference to selected Work in {contract.path}: "
                f"{token.content}"
            )


def _reference_plan(
    root: Path,
    contract: WorkSource,
    text: str,
    start: int,
    end: int,
    target: Path,
    works_by_path: dict[Path, WorkPlan],
    has_fragment: bool,
    selected_targets: list[tuple[Path, bool]],
) -> ReferencePlan:
    """Validate one canonical Work map row and render its proposed update.

    Args:
        root: Repository root used to store a relative source path.
        contract: Parent or dependency contract containing the row.
        text: Exact text covering the row's source span.
        start: Zero-based inclusive start line from the Markdown parser.
        end: Zero-based exclusive end line from the Markdown parser.
        target: Resolved selected Work path linked by the row.
        works_by_path: Proposed Work plans keyed by resolved path.
        has_fragment: Whether the selected link being planned has a fragment.
        selected_targets: All selected targets found in the row.

    Returns:
        A one-based, inclusive source span and its replacement text.

    Raises:
        ClosePlanningError: The row is noncanonical or has an unsafe link.
    """
    if has_fragment:
        raise ClosePlanningError(
            f"ambiguous reference to selected Work in {contract.path}: {text.strip()}"
        )
    match = re.fullmatch(
        r"\s*-\s+(?:\*\*)?(\S+?)(?:\*\*)?\s+"
        r"\[([^]]+)\]\(([^)]+)\):\s*(.+)\s*",
        text,
        re.DOTALL,
    )
    if match is None:
        raise ClosePlanningError(
            f"ambiguous Work map entry in {contract.path}: {text.strip()}"
        )
    status_text, title, raw_target, purpose = match.groups()
    primary_target, primary_has_fragment = _local_link_target(
        raw_target, root, contract.path.parent
    )
    if primary_target != target or selected_targets != [
        (primary_target, primary_has_fragment)
    ]:
        raise ClosePlanningError(
            f"ambiguous reference to selected Work in {contract.path}: {text.strip()}"
        )
    try:
        parse_criterion_status(status_text)
    except ValueError as exc:
        raise ClosePlanningError(
            f"ambiguous Work map entry in {contract.path}: {text.strip()}"
        ) from exc
    purpose = purpose.strip()
    work = works_by_path[target]
    status_label = (
        f"**{work.result}**" if text.lstrip().startswith("- **") else work.result
    )
    reason = f" (reason: {work.reason})" if work.reason else ""
    prefix = re.match(r"^(\s*-\s+)", text)
    if prefix is None:
        raise ClosePlanningError(
            f"ambiguous Work map entry in {contract.path}: {text.strip()}"
        )
    after_entry = (
        f"pending decision for {title}: {purpose}"
        if work.result == "PENDING"
        else f"{status_label} {title}: {purpose}{reason}"
    )
    after = f"{prefix.group(1)}{after_entry}"
    return ReferencePlan(
        contract.path.relative_to(root).as_posix(), start + 1, end, text, after
    )


def _pr_head(
    root: Path, paths: tuple[str, ...]
) -> tuple[str, int, str, str, str, str, str]:
    """Verify the clean branch and open PR metadata for selected contracts.

    Args:
        root: Repository root established for the selected Work paths.
        paths: Repository-relative selected contract paths.

    Returns:
        Origin repository, PR number, branch, local and remote tips, PR head
        repository, and PR head commit.

    Raises:
        ClosePlanningError: The branch, remote tip, or PR does not match.
    """
    branch = _run_git(["branch", "--show-current"])
    if not branch or branch == "master":
        raise ClosePlanningError("run work-close from the selected Work PR branch")
    status = _run_git(["status", "--porcelain=v1", "--untracked-files=all"])
    if status:
        raise ClosePlanningError("working tree or index is not clean")
    head = _run_git(["rev-parse", "HEAD"])
    remote = _run_git(["ls-remote", "--heads", "origin", f"refs/heads/{branch}"])
    remote_fields = remote.split()
    if (
        len(remote_fields) != 2
        or remote_fields[1] != f"refs/heads/{branch}"
        or remote_fields[0] != head
    ):
        raise ClosePlanningError("local and origin branch tips do not match exactly")
    remote_tip = remote_fields[0]
    repository = _github_repository(_run_git(["config", "--get", "remote.origin.url"]))
    number, changed, head_repo, pr_head = _pr_metadata(branch, head, repository)
    if not set(paths) <= changed:
        raise ClosePlanningError(
            "every selected contract must be changed in the current PR"
        )
    return repository, number, branch, head, remote_tip, head_repo, pr_head


def _github_repository(value: str) -> str:
    """Extract owner/repository from a supported GitHub remote URL.

    Args:
        value: HTTPS or SSH GitHub remote URL.

    Returns:
        The repository's owner/name identifier.

    Raises:
        ClosePlanningError: The remote URL is not a supported GitHub URL.
    """
    match = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:)([^/]+/[^/]+?)(?:\.git)?", value
    )
    if match is None:
        raise ClosePlanningError("origin must identify one supported GitHub repository")
    return match.group(1)


def _pr_metadata(
    branch: str, head: str, repository: str
) -> tuple[int, set[str], str, str]:
    """Verify the current open PR and return its changed paths and head.

    Args:
        branch: Current local branch name.
        head: Current local commit identifier.
        repository: Expected GitHub owner/repository identifier.

    Returns:
        PR number, changed paths, head repository, and PR head commit.

    Raises:
        ClosePlanningError: PR metadata is invalid or does not match inputs.
    """
    data = _json_command(
        ["gh", "pr", "view", "--json", "number,state,headRefName,headRefOid"],
        "cannot inspect the current open PR",
    )
    if not isinstance(data, dict):
        raise ClosePlanningError("current PR metadata has an invalid shape")
    number = data.get("number")
    if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
        raise ClosePlanningError("current PR number has an invalid shape")
    if (
        data.get("state") != "OPEN"
        or data.get("headRefName") != branch
        or data.get("headRefOid") != head
    ):
        raise ClosePlanningError("current open PR does not match the local branch head")
    changed, head_repo, pr_head = _pr_repository_details(repository, number, head)
    return number, changed, head_repo, pr_head


def _pr_repository_details(
    repository: str, number: int, local_head: str
) -> tuple[set[str], str, str]:
    """Read PR files and verify its base/head repository and commit identity.

    Args:
        repository: Expected GitHub owner/repository identifier.
        number: Open pull request number.
        local_head: Commit expected at the PR head.

    Returns:
        Paths from the first page of at most 100 changed files, head repository
        name, and PR head commit.

    Raises:
        ClosePlanningError: Repository, file, or PR head metadata is invalid.
    """
    repo_data = _json_command(
        ["gh", "repo", "view", "--json", "nameWithOwner"],
        "cannot inspect PR repository identity",
    )
    pull = _json_command(
        ["gh", "api", f"repos/{repository}/pulls/{number}"],
        "cannot inspect PR repository identity",
    )
    files = _json_command(
        ["gh", "api", f"repos/{repository}/pulls/{number}/files?per_page=100"],
        "cannot inspect PR repository identity",
    )
    if not isinstance(repo_data, dict) or repo_data.get("nameWithOwner") != repository:
        raise ClosePlanningError("gh repository does not match origin repository")
    head_repo, pr_head = _validate_pr_head(pull, repository, local_head)
    changed = _changed_paths(files)
    return changed, head_repo, pr_head


def _validate_pr_head(
    pull: object, repository: str, local_head: str
) -> tuple[str, str]:
    """Validate PR head/base repositories and require the expected head commit.

    Args:
        pull: Decoded GitHub pull request metadata.
        repository: Expected owner/repository identifier.
        local_head: Commit expected at the PR head.

    Returns:
        The PR head repository name and commit identifier.

    Raises:
        ClosePlanningError: Metadata is malformed or the identity does not match.
    """
    if not isinstance(pull, dict):
        raise ClosePlanningError("current PR metadata has an invalid shape")
    head_obj, base_obj = pull.get("head"), pull.get("base")
    head_repo_obj = head_obj.get("repo") if isinstance(head_obj, dict) else None
    base_repo_obj = base_obj.get("repo") if isinstance(base_obj, dict) else None
    if not isinstance(head_repo_obj, dict) or not isinstance(base_repo_obj, dict):
        raise ClosePlanningError(
            "PR head/base repository metadata has an invalid shape"
        )
    head_repo, base_repo = (
        head_repo_obj.get("full_name"),
        base_repo_obj.get("full_name"),
    )
    if not isinstance(head_obj, dict):
        raise ClosePlanningError("PR head metadata has an invalid shape")
    pr_head = head_obj.get("sha")
    if head_repo != repository or base_repo != repository:
        raise ClosePlanningError("PR head and base repositories must match origin")
    if not isinstance(head_repo, str) or not isinstance(pr_head, str):
        raise ClosePlanningError("PR head metadata has an invalid shape")
    if pr_head != local_head:
        raise ClosePlanningError("current open PR does not match the local branch head")
    return head_repo, pr_head


def _changed_paths(files: object) -> set[str]:
    """Validate a GitHub pull-request files response and collect filenames.

    Args:
        files: Decoded response expected to be a list of filename records.

    Returns:
        The filenames listed as changed in the pull request.

    Raises:
        ClosePlanningError: The response is not a list of filename records.
    """
    if not isinstance(files, list) or any(
        not isinstance(item, dict) or not isinstance(item.get("filename"), str)
        for item in files
    ):
        raise ClosePlanningError("current PR file metadata has an invalid shape")
    return {item["filename"] for item in files}


def _json_command(arguments: list[str], context: str) -> object:
    """Run a command and decode its standard output as JSON.

    Subprocess timeouts propagate unchanged.

    Args:
        arguments: Executable and arguments passed to the process adapter.
        context: Context prefixed to command or JSON decoding errors.

    Returns:
        The decoded JSON value.

    Raises:
        ClosePlanningError: The command fails or emits invalid JSON.
    """
    try:
        return json.loads(_run_process(arguments))
    except ValueError as exc:
        raise ClosePlanningError(f"{context}: {exc}") from exc


def _run_git(arguments: list[str]) -> str:
    """Run Git with the supplied arguments.

    Returns:
        The command's stripped standard output.
    """
    return _run_process(["git", *arguments])


def _run_process(arguments: list[str]) -> str:
    """Run a planning subprocess with optional Git locks disabled.

    Subprocess timeouts propagate unchanged.

    Args:
        arguments: Executable and arguments to run.

    Returns:
        The command's stripped standard output.

    Raises:
        ClosePlanningError: The process cannot run or exits unsuccessfully.
    """
    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        result = subprocess.run(
            arguments,
            check=True,
            capture_output=True,
            text=True,
            env=environment,
            timeout=15,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ClosePlanningError(f"command failed: {arguments[0]}: {exc}") from exc
    return result.stdout.strip()
