# SPDX-License-Identifier: Apache-2.0
"""Exercise read-only closure planning with real Git and a controlled PR boundary."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[4]


def test_make_work_close_reports_pending_then_confirmed_plan_without_writes(
    tmp_path: Path,
) -> None:
    # Given
    root, environment, selected, parent = _repository(tmp_path)
    before = _repository_state(root)

    # When
    pending = _run(root, environment, selected)
    confirmed = _run(root, environment, selected, "ABORT_REMAINING=true")

    # Then
    assert pending.returncode == 0
    assert "Closure plan: PENDING DECISION" in pending.stdout
    assert "AC-1: TODO -> TODO" in pending.stdout
    assert "Decision required: ask the maintainer" in pending.stdout
    assert confirmed.returncode == 0
    assert "Closure plan: READY" in confirmed.stdout
    assert "AC-1: TODO -> ABORT" in confirmed.stdout
    assert "Maintainer confirmed abort during authorized closure." in confirmed.stdout
    assert (
        "+ - **ABORT** Child work: child purpose,\n  preserving the full purpose text."
        in confirmed.stdout
    )
    assert _repository_state(root) == before
    assert parent.read_text(encoding="utf-8").endswith(
        "- **TODO** [Child work](child/README.md): child purpose,\n"
        "  preserving the full purpose text.\n"
    )


def test_existing_abort_does_not_hide_an_unresolved_todo(tmp_path: Path) -> None:
    # Given
    root, environment, selected, _ = _repository(tmp_path, criterion_status="ABORT")
    contract = root / selected
    contract.write_text(
        contract.read_text(encoding="utf-8")
        + "\n### **AC-2 TODO** Remaining\n\nStill required.\n",
        encoding="utf-8",
    )
    _git(root, "add", selected)
    _git(root, "commit", "-m", "docs: leave one criterion unresolved")
    _git(root, "push", "origin", "HEAD:refs/heads/work/fixture")
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 0
    assert "Closure plan: PENDING DECISION" in result.stdout
    assert "AC-1: ABORT -> ABORT" in result.stdout
    assert "AC-2: TODO -> TODO" in result.stdout
    assert _repository_state(root) == before


def test_make_work_close_plans_done_work_and_reference_without_writes(
    tmp_path: Path,
) -> None:
    # Given
    root, environment, selected, _ = _repository(tmp_path, criterion_status="DONE")
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 0
    assert "Closure plan: READY" in result.stdout
    assert "DONE doc/feat/parent/child/README.md: Child work" in result.stdout
    assert "AC-1: DONE -> DONE" in result.stdout
    assert (
        "+ - **DONE** Child work: child purpose,\n  preserving the full purpose text."
        in result.stdout
    )
    assert _repository_state(root) == before


def test_make_work_close_accepts_unbold_multiline_map_and_angle_encoded_destination(
    tmp_path: Path,
) -> None:
    # Given
    root, environment, selected, _ = _repository(
        tmp_path, criterion_status="DONE", bold_map=False
    )
    parent = root / "doc/feat/parent/README.md"
    parent.write_text(
        "# Parent\n\n## Children\n\n"
        "- DONE [Child work](<child/%52EADME.md>): child purpose,\n"
        "  preserving the full purpose text.\n",
        encoding="utf-8",
    )
    _git(root, "add", parent.relative_to(root).as_posix())
    _git(root, "commit", "-m", "docs: use encoded angle reference")
    _git(root, "push", "origin", "HEAD:refs/heads/work/fixture")
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 0
    assert "  doc/feat/parent/README.md\n" in result.stdout
    assert "- DONE [Child work](<child/%52EADME.md>): child purpose,\n" in result.stdout
    assert (
        "+ - DONE Child work: child purpose,\n  preserving the full purpose text."
        in result.stdout
    )
    assert _repository_state(root) == before


def test_make_work_close_keeps_selected_work_results_independent(
    tmp_path: Path,
) -> None:
    # Given
    root, environment, selected, _ = _repository(tmp_path)
    other = "doc/feat/other/README.md"
    other_path = root / other
    other_path.parent.mkdir(parents=True)
    fixture = Path(__file__).resolve().parents[2] / "fixtures/work_close/child_work.md"
    other_path.write_text(
        fixture.read_text(encoding="utf-8").replace("AC-1 TODO", "AC-1 ABORT"),
        encoding="utf-8",
    )
    _git(root, "add", other)
    _git(root, "commit", "-m", "docs: add aborted Work")
    _git(root, "push", "origin", "HEAD:refs/heads/work/fixture")
    environment["GH_CHANGED_PATHS"] = f"{selected},{other}"
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected, other)

    # Then
    assert result.returncode == 0
    assert f"PENDING {selected}" in result.stdout
    assert f"ABORT {other}" in result.stdout
    assert _repository_state(root) == before


def test_make_work_close_refuses_a_dirty_index_or_working_tree(
    tmp_path: Path,
) -> None:
    # Given
    root, environment, selected, _ = _repository(tmp_path)
    contract = root / selected
    contract.write_text(
        contract.read_text(encoding="utf-8") + "\nLocal edit.\n", encoding="utf-8"
    )
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 2
    assert "working tree or index is not clean" in result.stderr
    assert _repository_state(root) == before


@pytest.mark.parametrize("dirty_kind", ["staged", "untracked"])
def test_make_work_close_refuses_index_and_untracked_changes(
    tmp_path: Path, dirty_kind: str
) -> None:
    # Given: the parameter and helper create either staged or untracked dirtiness.
    root, environment, selected, _ = _repository(tmp_path)
    dirty_file = root / "local-note.md"
    dirty_file.write_text("local state\n", encoding="utf-8")
    if dirty_kind == "staged":
        _git(root, "add", "local-note.md")
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 2
    assert "working tree or index is not clean" in result.stderr
    assert _repository_state(root) == before


def test_make_work_close_rejects_invalid_and_escaping_symlink_selections(
    tmp_path: Path,
) -> None:
    # Given
    root, environment, _, _ = _repository(tmp_path)
    outside = tmp_path / "outside/README.md"
    outside.parent.mkdir()
    outside.write_text("# Outside\n", encoding="utf-8")
    link = root / "doc/feat/parent/escape/README.md"
    link.parent.mkdir()
    link.symlink_to(outside)
    before = _repository_state(root)

    # When
    invalid = _run(root, environment, "doc/feat/parent/child/contract.md")
    escaping = _run(root, environment, "doc/feat/parent/escape/README.md")

    # Then
    assert invalid.returncode == 2
    assert "select each Work README.md explicitly" in invalid.stderr
    assert escaping.returncode == 2
    assert "outside the Work root" in escaping.stderr
    assert _repository_state(root) == before


def test_make_work_close_refuses_ambiguous_selected_contract_reference(
    tmp_path: Path,
) -> None:
    # Given
    root, environment, selected, parent = _repository(tmp_path)
    parent.write_text(
        parent.read_text(encoding="utf-8").replace("## Children", "## Links"),
        encoding="utf-8",
    )
    _git(root, "add", parent.relative_to(root).as_posix())
    _git(root, "commit", "-m", "docs: add ambiguous Work reference")
    _git(root, "push", "origin", "HEAD:refs/heads/work/fixture")
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 2
    assert "ambiguous reference to selected Work" in result.stderr
    assert _repository_state(root) == before


def test_make_work_close_refuses_contract_missing_from_current_pr(
    tmp_path: Path,
) -> None:
    # Given
    root, environment, selected, _ = _repository(tmp_path)
    environment["GH_CHANGED_PATH"] = "doc/feat/other/README.md"
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 2
    assert "every selected contract must be changed in the current PR" in result.stderr
    assert _repository_state(root) == before


def test_make_work_close_refuses_pr_head_outside_the_local_branch_tip(
    tmp_path: Path,
) -> None:
    # Given
    root, environment, selected, _ = _repository(tmp_path)
    environment["GH_HEAD_REF_OID"] = "0" * 40
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 2
    assert "current open PR does not match the local branch head" in result.stderr
    assert _repository_state(root) == before


def test_make_work_close_refuses_remote_branch_tip_drift(tmp_path: Path) -> None:
    # Given
    root, environment, selected, _ = _repository(tmp_path)
    remote = _git(root, "remote", "get-url", "origin")
    diverged = tmp_path / "diverged"
    subprocess.run(
        ["git", "clone", "--branch", "work/fixture", remote, str(diverged)],
        check=True,
        capture_output=True,
        timeout=30,
    )
    _git(diverged, "config", "user.name", "Fixture")
    _git(diverged, "config", "user.email", "fixture@example.invalid")
    (diverged / "remote-change.txt").write_text("remote tip moved\n", encoding="utf-8")
    _git(diverged, "add", ".")
    _git(diverged, "commit", "-m", "docs: move remote tip")
    push = subprocess.run(
        ["git", "push", "origin", "HEAD:refs/heads/work/fixture"],
        cwd=diverged,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert push.returncode == 0, push.stderr
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 2
    assert "local and origin branch tips do not match exactly" in result.stderr
    assert _repository_state(root) == before


def test_make_work_close_refuses_noncanonical_live_markdown_reference(
    tmp_path: Path,
) -> None:
    # Given
    root, environment, selected, _ = _repository(tmp_path, prose_reference=True)
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 2
    assert "ambiguous reference to selected Work" in result.stderr
    assert _repository_state(root) == before


def test_make_work_close_inspects_root_readme_and_reference_style_links(
    tmp_path: Path,
) -> None:
    # Given: the fixture provides a tracked root reference-style link.
    root, environment, selected, _ = _repository(tmp_path)
    shutil.copyfile(
        Path(__file__).resolve().parents[2] / "fixtures/work_close/root_readme.md",
        root / "README.md",
    )
    readme = root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "child/README.md",
            "doc/feat/parent/child/README.md",
        ),
        encoding="utf-8",
    )
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "docs: add root reference")
    _git(root, "push", "origin", "HEAD:refs/heads/work/fixture")
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 2
    assert "ambiguous reference to selected Work" in result.stderr
    assert _repository_state(root) == before


def test_make_work_close_refuses_live_html_reference(tmp_path: Path) -> None:
    # Given
    root, environment, selected, _ = _repository(tmp_path)
    guide = root / "doc/guide.md"
    guide.write_text(
        '<a href="feat/parent/child/README.md">Child work</a>\n',
        encoding="utf-8",
    )
    _git(root, "add", guide.relative_to(root).as_posix())
    _git(root, "commit", "-m", "docs: add HTML reference")
    _git(root, "push", "origin", "HEAD:refs/heads/work/fixture")
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 2
    assert "ambiguous reference to selected Work" in result.stderr
    assert _repository_state(root) == before


def test_make_work_close_refuses_html_block_reference(tmp_path: Path) -> None:
    # Given
    root, environment, selected, _ = _repository(tmp_path, criterion_status="DONE")
    guide = root / "doc/guide.md"
    guide.write_text(
        '<div>\n<a href="feat/parent/child/README.md">Child</a>\n</div>\n',
        encoding="utf-8",
    )
    _git(root, "add", guide.relative_to(root).as_posix())
    _git(root, "commit", "-m", "docs: add block HTML reference")
    _git(root, "push", "origin", "HEAD:refs/heads/work/fixture")
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 2
    assert "ambiguous reference to selected Work" in result.stderr
    assert _repository_state(root) == before


def test_make_work_close_refuses_repository_root_relative_reference(
    tmp_path: Path,
) -> None:
    # Given
    root, environment, selected, _ = _repository(tmp_path, criterion_status="DONE")
    guide = root / "doc/guide.md"
    guide.write_text("[Child](/doc/feat/parent/child/README.md)\n", encoding="utf-8")
    _git(root, "add", guide.relative_to(root).as_posix())
    _git(root, "commit", "-m", "docs: add root-relative reference")
    _git(root, "push", "origin", "HEAD:refs/heads/work/fixture")
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 2
    assert "ambiguous reference to selected Work" in result.stderr
    assert _repository_state(root) == before


def test_selected_link_in_map_purpose_is_not_rewritten_as_primary_entry(
    tmp_path: Path,
) -> None:
    # Given
    root, environment, selected, parent = _repository(tmp_path, criterion_status="DONE")
    parent.write_text(
        "# Parent\n\n## Dependencies\n\n"
        "- **TODO** [Other](other/README.md): uses "
        "[Child](child/README.md).\n",
        encoding="utf-8",
    )
    _git(root, "add", parent.relative_to(root).as_posix())
    _git(root, "commit", "-m", "docs: add selected link in purpose")
    _git(root, "push", "origin", "HEAD:refs/heads/work/fixture")
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 2
    assert "ambiguous reference to selected Work" in result.stderr
    assert _repository_state(root) == before


def test_nested_map_updates_must_not_overlap(tmp_path: Path) -> None:
    # Given
    root, environment, selected, parent = _repository(tmp_path, criterion_status="DONE")
    other = "doc/feat/parent/other/README.md"
    other_path = root / other
    other_path.parent.mkdir(parents=True)
    shutil.copyfile(root / selected, other_path)
    parent.write_text(
        "# Parent\n\n## Children\n\n"
        "- **TODO** [Child](child/README.md): purpose.\n"
        "  - **TODO** [Other](other/README.md): nested purpose.\n",
        encoding="utf-8",
    )
    _git(root, "add", ".")
    _git(root, "commit", "-m", "docs: add nested selected map entries")
    _git(root, "push", "origin", "HEAD:refs/heads/work/fixture")
    environment["GH_CHANGED_PATHS"] = f"{selected},{other}"
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected, other)

    # Then
    assert result.returncode == 2
    assert "overlapping Work map entries" in result.stderr
    assert _repository_state(root) == before


def test_nested_unselected_map_link_keeps_its_list_structure_in_plan(
    tmp_path: Path,
) -> None:
    # Given
    root, environment, selected, parent = _repository(tmp_path, criterion_status="DONE")
    other_path = root / "doc/feat/parent/other/README.md"
    other_path.parent.mkdir(parents=True)
    other_path.write_text("# Other work\n", encoding="utf-8")
    parent.write_text(
        "# Parent\n\n## Children\n\n"
        "- **TODO** [Child](child/README.md): purpose.\n"
        "  - **TODO** [Other](other/README.md): nested purpose.\n",
        encoding="utf-8",
    )
    _git(root, "add", ".")
    _git(root, "commit", "-m", "docs: nest an unselected map entry")
    _git(root, "push", "origin", "HEAD:refs/heads/work/fixture")
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 0
    assert (
        "+ - **DONE** Child: purpose.\n"
        "  - **TODO** [Other](other/README.md): nested purpose." in result.stdout
    )
    assert _repository_state(root) == before


def test_make_work_close_ignores_fenced_markdown_examples(tmp_path: Path) -> None:
    # Given: the fixture contains a link-shaped fenced code example.
    root, environment, selected, _ = _repository(tmp_path)
    guide = root / "doc/guide.md"
    shutil.copyfile(
        Path(__file__).resolve().parents[2] / "fixtures/work_close/fenced_reference.md",
        guide,
    )
    _git(root, "add", guide.relative_to(root).as_posix())
    _git(root, "commit", "-m", "docs: add fenced example")
    _git(root, "push", "origin", "HEAD:refs/heads/work/fixture")
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 0
    assert "Reference updates:\n" in result.stdout
    assert "fenced_reference.md" not in result.stdout
    assert _repository_state(root) == before


@pytest.mark.parametrize(
    ("environment_key", "message"),
    [
        ("GH_HEAD_REPOSITORY", "PR head and base repositories must match origin"),
        ("GH_REPOSITORY", "gh repository does not match origin repository"),
    ],
)
def test_make_work_close_refuses_mismatched_repository_metadata(
    tmp_path: Path, environment_key: str, message: str
) -> None:
    # Given: metadata from the parameter conflicts with origin identity.
    root, environment, selected, _ = _repository(tmp_path)
    environment[environment_key] = "fork/work-close-fixture"
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 2
    assert message in result.stderr
    assert _repository_state(root) == before


@pytest.mark.parametrize(
    ("environment_key", "environment_value", "reason"),
    [
        ("GH_PR_STATE", "CLOSED", "current open PR does not match"),
        ("GH_PR_MALFORMED", "1", "current PR number has an invalid shape"),
    ],
)
def test_make_work_close_refuses_closed_or_malformed_pr(
    tmp_path: Path, environment_key: str, environment_value: str, reason: str
) -> None:
    # Given: the parameter controls the fake PR response.
    root, environment, selected, _ = _repository(tmp_path)
    environment[environment_key] = environment_value
    before = _repository_state(root)

    # When
    result = _run(root, environment, selected)

    # Then
    assert result.returncode == 2
    assert reason in result.stderr
    assert _repository_state(root) == before


def test_make_work_close_quotes_invalid_abort_flag_without_shell_effect(
    tmp_path: Path,
) -> None:
    # Given
    root, environment, selected, _ = _repository(tmp_path)
    marker = tmp_path / "injected"
    before = _repository_state(root)
    hostile = f"ABORT_REMAINING=false'; touch {marker}; #"

    # When
    result = subprocess.run(
        [
            "make",
            "-f",
            str(ROOT / "Makefile"),
            "work-close",
            f"ARGS={selected}",
            hostile,
        ],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Then
    assert result.returncode == 2
    assert not marker.exists()
    assert _repository_state(root) == before


def _repository(
    tmp_path: Path,
    *,
    prose_reference: bool = False,
    criterion_status: str = "TODO",
    bold_map: bool = True,
) -> tuple[Path, dict[str, str], str, Path]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "master")
    _git(root, "config", "user.name", "Fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _write_contracts(root, prose_reference, criterion_status, bold_map)
    _git(root, "add", ".")
    _git(root, "commit", "-m", "docs: add fixture Work contracts")
    _git(root, "switch", "-c", "work/fixture")
    remote = tmp_path / "origin.git"
    subprocess.run(
        ["git", "init", "--bare", str(remote)],
        check=True,
        capture_output=True,
        timeout=30,
    )
    _git(
        root,
        "remote",
        "add",
        "origin",
        "https://github.com/example/work-close-fixture.git",
    )
    _git(
        root,
        "config",
        "url." + remote.as_posix() + ".insteadOf",
        "https://github.com/example/work-close-fixture.git",
    )
    _git(root, "push", "-u", "origin", "work/fixture")
    fake_bin = _fake_gh(tmp_path)
    environment = os.environ | {
        "PATH": (
            f"{ROOT / '.venv' / 'bin'}{os.pathsep}{fake_bin}"
            f"{os.pathsep}{os.environ['PATH']}"
        ),
        "PYTHONPATH": str(ROOT),
        "VIRTUAL_ENV": str(ROOT / ".venv"),
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "HOME": str(tmp_path / "home"),
        "UV_CACHE_DIR": str(tmp_path / "uv-cache"),
    }
    Path(environment["HOME"]).mkdir()
    return (
        root,
        environment,
        "doc/feat/parent/child/README.md",
        root / "doc/feat/parent/README.md",
    )


def _write_contracts(
    root: Path, prose_reference: bool, criterion_status: str, bold_map: bool
) -> None:
    parent = root / "doc/feat/parent/README.md"
    child = root / "doc/feat/parent/child/README.md"
    parent.parent.mkdir(parents=True)
    child.parent.mkdir(parents=True)
    fixture = Path(__file__).resolve().parents[2] / "fixtures/work_close"
    parent_text = (fixture / "parent.md").read_text(encoding="utf-8")
    if not bold_map:
        parent_text = parent_text.replace("**TODO**", "TODO")
    parent.write_text(parent_text, encoding="utf-8")
    child_text = (fixture / "child_work.md").read_text(encoding="utf-8")
    child.write_text(
        child_text.replace("AC-1 TODO", f"AC-1 {criterion_status}"),
        encoding="utf-8",
    )
    if prose_reference:
        guide = root / "doc/guide.md"
        guide.parent.mkdir(parents=True, exist_ok=True)
        guide.write_text(
            "# Guide\n\nRelated [Child work](feat/parent/child/README.md).\n",
            encoding="utf-8",
        )


def _fake_gh(tmp_path: Path) -> Path:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_gh = fake_bin / "gh"
    shutil.copyfile(
        Path(__file__).resolve().parents[2] / "fixtures/work_close/fake_gh.py", fake_gh
    )
    fake_gh.chmod(0o755)
    return fake_bin


def _repository_state(root: Path) -> tuple[dict[str, bytes], bytes, str, str, str]:
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts and ".cache" not in path.parts
    }
    status = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    index = _git(root, "write-tree")
    index_bytes = (root / ".git/index").read_bytes()
    head = _git(root, "rev-parse", "HEAD")
    remote = _git(root, "ls-remote", "origin", "refs/heads/work/fixture")
    return files, index_bytes, status, index, f"{head}:{remote}"


def _run(root: Path, environment: dict[str, str], selection: str, *flags: str):
    abort_flag = ["ABORT_REMAINING=true"] if "ABORT_REMAINING=true" in flags else []
    selections = [flag for flag in flags if flag != "ABORT_REMAINING=true"]
    return subprocess.run(
        [
            "make",
            "-f",
            str(ROOT / "Makefile"),
            "work-close",
            f"ARGS={' '.join((selection, *selections))}",
            *abort_flag,
        ],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def _git(root: Path, *arguments: str) -> str:
    environment = os.environ | {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
    }
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
    )
    return result.stdout.strip()
