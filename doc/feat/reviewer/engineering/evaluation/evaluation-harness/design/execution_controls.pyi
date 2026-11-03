"""PROPOSED AC-10/11 boundary additions, not an implemented module.

These sketches extend the runtime owners named in architecture.md. They do not
replace the historical design/eval package or define another public framework.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from script.eval.model import FrozenPlan, HarnessConfig, PlannedCall, PreparedEvidence
from script.eval.runner.ports import CliBinding, EffectiveCall

SandboxMode = Literal["read-only", "workspace-write"]
ToolProfile = Literal["local-tools-disabled-v1", "local-tools-enabled-v1"]

@dataclass(frozen=True)
class RequestedControls:
    """Fields added to HarnessConfig and retained once via FrozenPlan.configuration.

    None selects one future owned empty directory for the run. An explicit
    path is retained as requested, including a relative path. For example,
    RequestedControls(Path("clone"), "workspace-write", True) borrows clone.
    """

    working_directory: Path | None = None
    sandbox_mode: SandboxMode = "read-only"
    enable_tools: bool = False

@dataclass(frozen=True)
class PreparedWorkspace:
    """Execution-time selection after resolving against the caller's launch cwd.

    cwd is the actual absolute directory. owned is true only for a temporary
    directory created by the standalone owner. It remains alive until all
    retained call tasks and their cleanup settle. A borrowed directory is never
    created, chmodded, cleaned, or deleted by the harness.
    """

    cwd: Path
    owned: bool

@dataclass(frozen=True)
class InvocationControls:
    """Bound requested controls; effective sandbox and tool state stay unknown.

    identity_workspace is the literal owned policy or resolved supplied path,
    never the random owned cwd. profile fixes the versioned adapter recipe.
    Runtime evidence retains cwd through the existing process record.
    """

    sandbox_mode: SandboxMode
    profile: ToolProfile
    identity_workspace: Literal["owned-empty-per-run-v1"] | Path
    cwd: Path

def validate_workspace_selection(
    config: HarnessConfig, launch_cwd: Path, /
) -> Path | None:
    """Resolve and check an explicit existing directory, including in dry run.

    Reject writable workspace with concurrency greater than one even when tools
    are disabled. Reject an output destination within a writable workspace.
    No owned directory or output is created. A missing path returns None.
    Filesystem and path errors refuse dispatch.
    """
    ...

def bind_invocation_controls(
    config: HarnessConfig, workspace: PreparedWorkspace, /
) -> InvocationControls:
    """Select the profile and stable workspace identity for this execution."""
    ...

def build_controlled_attempt(
    plan: FrozenPlan,
    call: PlannedCall,
    binding: CliBinding,
    evidence: PreparedEvidence,
    controls: InvocationControls,
    /,
) -> EffectiveCall:
    """Extend the existing request builder with controls and identity inputs.

    The builder is pure. It uses staged instruction paths without reading them.
    Historical v1/v2 records keep their existing validation and identity rules.
    """
    ...
