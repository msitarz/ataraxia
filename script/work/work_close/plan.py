# SPDX-License-Identifier: Apache-2.0
"""Read-only closure planning over Work contracts and repository metadata."""

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
    result = _run_git(["rev-parse", "--show-toplevel"])
    root = Path(result).resolve(strict=True)
    if Path.cwd().resolve() != root:
        raise ClosePlanningError("run work-close from the repository root")
    return root


def _selected_contracts(
    root: Path, selections: Sequence[str]
) -> tuple[WorkSource, ...]:
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
    criteria: list[CriterionPlan] = []
    for criterion in checked:
        status = criterion.status
        result = "ABORT" if status == "ABORT" else status
        if status == "TODO" and abort_remaining:
            result = "ABORT"
        criteria.append(CriterionPlan(criterion.identifier, status, result))
    return criteria


def _work_result(criteria: list[CriterionPlan]) -> WorkResult:
    if any(item.result == "ABORT" for item in criteria):
        return "ABORT"
    if any(item.result == "TODO" for item in criteria):
        return "PENDING"
    return "DONE"


def _work_reason(criteria: list[CriterionPlan], result: WorkResult) -> str | None:
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
    return path.name == "README.md" and path.is_relative_to(root / "doc" / "feat")


def _contract_references(
    root: Path,
    contract: WorkSource,
    selected_paths: set[Path],
    works_by_path: dict[Path, WorkPlan],
    is_work_contract: bool,
) -> list[ReferencePlan]:
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

    Returns:
        List item spans, current level-two headings, and inline tokens.
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
    parts = urlsplit(raw.strip("<>"))
    decoded = unquote(parts.path)
    if parts.scheme or parts.netloc or not decoded.endswith("README.md"):
        return None, False
    base = root if decoded.startswith("/") else parent
    relative = decoded.lstrip("/") if decoded.startswith("/") else decoded
    return (base / relative).resolve(), bool(parts.fragment)


def _html_hrefs(source: str) -> list[str]:
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
    match = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:)([^/]+/[^/]+?)(?:\.git)?", value
    )
    if match is None:
        raise ClosePlanningError("origin must identify one supported GitHub repository")
    return match.group(1)


def _pr_metadata(
    branch: str, head: str, repository: str
) -> tuple[int, set[str], str, str]:
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
    if not isinstance(files, list) or any(
        not isinstance(item, dict) or not isinstance(item.get("filename"), str)
        for item in files
    ):
        raise ClosePlanningError("current PR file metadata has an invalid shape")
    return {item["filename"] for item in files}


def _json_command(arguments: list[str], context: str) -> object:
    try:
        return json.loads(_run_process(arguments))
    except ValueError as exc:
        raise ClosePlanningError(f"{context}: {exc}") from exc


def _run_git(arguments: list[str]) -> str:
    return _run_process(["git", *arguments])


def _run_process(arguments: list[str]) -> str:
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
